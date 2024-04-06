# Slack Bot for GitHub Operations

This Slack bot integrates with GitHub to perform various repository operations such as cloning, modifying files, creating branches, committing changes, pushing branches, creating pull requests, and merging pull requests based on user commands in Slack.

## Prerequisites
- Python 3.x
- `slack_bolt`, `dotenv`, `gitpython`, and `requests` Python packages
- Slack App token and Bot token
- GitHub token
- Environment variables for repository owner, repository name, and other configurations

## Usage
1. Install the required Python packages:
   ```bash
   pip install slack_bolt python-dotenv GitPython requests
   ```
   or
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your Slack App with appropriate permissions and generate Slack App token and Bot token.

3. Set up your GitHub token with necessary permissions for repository operations.

4. Rename `.env.example` to `.env` & configure the environment variables from the file.

5. Run the script to start the Slack bot:
   ```bash
   python main.py
   ```

## Commands
### `/ecr`
- Command to search Amazon Elastic Container Registry (ECR) for artifacts.

### `/deploy <app> <env> <docker_image>`
- Command to deploy a Docker image for a specific application in a given environment.
- Parameters:
  - `<app>`: Name of the application (e.g., app1, app2, app3)
  - `<env>`: Environment (e.g., qa, stage, prod)
  - `<docker_image>`: Docker image to deploy

## Functionality
- Clones the GitHub repository corresponding to the specified environment.
- Modifies the `values.yaml` file in the repository to update the Docker image.
- Creates a new branch for deployment.
- Commits the changes with appropriate messages.
- Pushes the changes to the GitHub branch.
- Creates a pull request with the deployment changes.
- Merges the pull request upon approval.
