from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from git import Repo
from datetime import datetime
import os
import requests
import shutil
import threading

load_dotenv()
app_token = os.getenv("SLACK_APP_TOKEN")
bot_token = os.getenv("SLACK_BOT_TOKEN")
github_token = os.getenv("GITHUB_TOKEN")
repo_owner = os.getenv("REPO_OWNER")
repo_name = os.getenv("REPO_NAME")

valid_services = {"app1", "app2", "app3"}
valid_envs = {"qa", "stage", "prod"}

# Lock to prevent race conditions
git_lock = threading.Lock()

app = App(token=bot_token )

@app.command("/ecr")
def custom_command_function(ack, respond, command):
    ack()
    #TODO implement the logic to search ECR for your artifact
    respond("Looking for your artifact...")

def create_branch(repo, branch_name):
    try:
        if branch_name in [branch.name for branch in repo.branches]:
            raise ValueError(f"Branch '{branch_name}' already exists.")
        repo.create_head(branch_name)
        return True, None
    except Exception as e:
        return False, e

def create_commit(respond, repo, branch_name, app_name, docker_image):
    try:
        # Find changed file in repository and add it to git index
        changed_files = [item.a_path for item in repo.index.diff(None)]

        # Add changed files to the staging area
        for file in changed_files:
            repo.git.add(file)        
        repo.git.checkout(f'{branch_name}')
        repo.index.commit(f"Update {app_name} image to {docker_image}")

        return True, None
    except Exception as e:
        return False, e

def push_branch(respond, repo, branch_name):
    try:
        origin = repo.remote()
        origin.push(branch_name)
        print(f"Branch {branch_name} pushed to GitHub, URL: {origin.url}/tree/{branch_name}")

        return True, None
    except Exception as e:
        return False, e

def handle_git_operations(respond, repo, branch_name, app_name, image):
    try:
        # Create branch
        success, error = create_branch(repo, branch_name)
        if not success:
            raise Exception(f"Error creating branch: {error}")

        # Create commit
        success, error = create_commit(respond, repo, branch_name, app_name, image)
        if not success:
            raise Exception(f"Error creating commit: {error}")
        
        # Push changes to branch
        success, error = push_branch(respond, repo, branch_name)
        if not success:
            raise Exception(f"Error pushing changes to branch: {error}")

        # Create pull request
        pull_request_title = f"Update {app_name} image to {image}"
        pull_request_description = f"Update {app_name} image to {image}"
        pull_request_number = create_pull_request(respond, pull_request_title, pull_request_description, branch_name)

        # Merge pull request
        merge_pull_request(respond, pull_request_number)
        return True, None
    except Exception as e:
        return False, e

@app.command("/deploy")
def custom_command_function(ack, respond, command):
    ack()
    text = command.get("text", "").split()
    if len(text) != 3:
        respond("Invalid format. Usage: /deploy <app> <env> <docker_image>")
        return
    
    if text[0] not in valid_services:
        respond(f"Invalid service: {text[0]}. Valid services:")
        respond(format_list_as_bullet_points(valid_services))
        return
    
    if text[1] not in valid_envs:
        respond(f"Invalid env: {text[1]}. Valid envs:")
        respond(format_list_as_bullet_points(valid_envs))
        return

    app_name, env, image = text

    # Generate branch name
    time = datetime.now().strftime("%Y%m%d%H%M%S")
    branch_name = f"deploy-{app_name}-{env}-{time}"

    repo_url = get_repo_url(env)
    clone_path = f"./cloned_repos/{repo_name}"
    create_or_clear_directory(clone_path)
    try:
        respond(f"Deploying {image} for {app_name} on {env}")
        git_lock.acquire()

        # Clone repository
        repo = Repo.clone_from(repo_url, clone_path)
        respond(f"Repository {repo_url} cloned successfully to {clone_path}")

        try:
            # Modify the file
            values_file_path = os.path.join(clone_path, f"values.yaml")
            modify_values_file(respond, values_file_path, image)
        except Exception as modify_error:
            respond(f"Error modifying values file: {str(modify_error)}")
            return

        # Handle git operations
        success, error = handle_git_operations(respond, repo, branch_name, app_name, image)
        if not success:
            respond(f"Error deploying changes: {error}")
            return
    except Exception as e:
        respond(f"Error deploying changes: {str(e)}")
    finally:
        git_lock.release()

def create_or_clear_directory(directory):
    try:
        if os.path.exists(directory):
            # If the directory exists, remove all its contents
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                else:
                    shutil.rmtree(item_path)
        else:
            os.makedirs(directory)
    except PermissionError as e:
        print(f"Permission error: {e}")

def create_pull_request(respond, title, body, branch):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": f'{title}',
        "body": f'{body}',
        "head": f'{branch}',
        "base": "master"
    }
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 201:
        pr_data = response.json()
        pull_request_number = pr_data['number']
        respond(f"Pull request created successfully")
        return pull_request_number
    elif response.status_code == 422:
        respond("Failed to create pull request. No commits between master and the head branch.")
    else:
        error_message = f"Failed to create pull request. Status code: {response.status_code}\n"
        error_message += f"Error message: {response.text}"
        respond(error_message)
    return None

def merge_pull_request(respond, pull_request_number):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pull_request_number}/merge"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.put(url, headers=headers)
    print(response.status_code)
    if response.status_code == 200:
        respond(f"Pull request merged successfully")
    else:
        respond(f"Pull request failed to merge. Error: {response.text}")

def format_list_as_bullet_points(items):
    return "\n".join([f"• {item}" for item in items])

def get_repo_url(env):
    QA_REPO = f'https://github.com/{repo_owner}/{repo_name}.git'
    # STAGE_REPO = f'https://github.com/{repo_owner}/{repo_name_1}.git'
    # PROD_REPO = f'https://github.com/{repo_owner}/{repo_name_2}.git'
    repo_urls = {
        "qa": QA_REPO,
        # "stage": STAGE_REPO,
        # "prod": PROD_REPO
    }
    return repo_urls.get(env, "")

def modify_values_file(respond, file_path, value):
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith("image:"):
                lines[i] = f"image: {value}\n"

        with open(file_path, "w") as f:
            f.writelines(lines)
        respond("Values file modified successfully.")

    except Exception as e:
        print(f"Error modifying file: {str(e)}")

def main():
    handler = SocketModeHandler(app, app_token)
    handler.start()

if __name__ == '__main__':
    main()
