import os
import sys
import subprocess
import time
import logging

logging.basicConfig(level=logging.INFO)

SLEEP_DURATION = 2

def has_tf_files(directory):
    """Check if a directory contains .tf files."""
    for file in os.listdir(directory):
        if file.endswith('.tf'):
            return True
    return False

def execute_terraform_init(directory):
    """Execute terraform init."""
    logging.info(f"Executing terraform init in {directory}")
    try:
        subprocess.run(['terraform', 'init', '--upgrade'], cwd=directory, check=True)
        time.sleep(SLEEP_DURATION)
        execute_terraform_plan(directory)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing terraform init in {directory}: {e}")

def execute_terraform_plan(directory):
    """Execute terraform plan and save output to a file."""
    logging.info(f"Executing terraform plan in {directory}")
    try:
        plan_process = subprocess.run(['terraform', 'plan', '-no-color'], cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        with open(f"{directory}/terraform_plan_output.txt", "w") as f:
            f.write(plan_process.stdout.decode())
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing terraform plan in {directory}: {e}")

def process_directory(directory):
    """Process a directory."""
    execute_terraform_init(directory)
    time.sleep(SLEEP_DURATION)

def main():
    """Terraform init & plan for all directories in the base directory."""
    if not os.path.isdir(BASE_DIRECTORY):
        print("Error: Root directory does not exist.")
        sys.exit(1)
    
    good_directories = []

    for root, dirs, _ in os.walk(BASE_DIRECTORY):
        if '.terraform' in dirs:
            process_directory(root)
            dirs.clear()  # Exclude further subdirectories
            continue

        if has_tf_files(root):
            good_directories.append(root)

    for directory in good_directories:
        process_directory(directory)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tf_plan.py <base_directory>")
        sys.exit(1)

    BASE_DIRECTORY = sys.argv[1]

    main()
