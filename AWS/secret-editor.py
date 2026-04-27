#!/usr/bin/env python3
"""Interactive tool to edit AWS Secrets Manager secrets safely.

No more escaping issues — you edit real JSON in your editor.
PEM certs/keys are shown as actual multi-line text in the editor,
and converted back to \\n-delimited strings when saving.

Set EDITOR env var to your preference:
  export EDITOR=nano
  export EDITOR="code --wait"
Defaults to vim if EDITOR is not set.

Usage:
  python3 secret-editor.py
"""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"


def truncate(val, max_lines=5):
    """Truncate a value for display, showing line count if long."""
    lines = val.splitlines()
    if len(lines) <= max_lines:
        return val
    shown = "\n".join(lines[:max_lines])
    return f"{shown}\n... ({len(lines)} lines total)"


def show_change(key, old_val, new_val):
    """Show a clear BEFORE/AFTER comparison for a key."""
    print(f"\n{BOLD}  {key}:{RESET}")
    print(f"{RED}    BEFORE:{RESET}")
    for line in truncate(old_val).splitlines():
        print(f"{RED}      {line}{RESET}")
    print(f"{GREEN}    AFTER:{RESET}")
    for line in truncate(new_val).splitlines():
        print(f"{GREEN}      {line}{RESET}")


def prompt(msg, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"{msg}{suffix}: ").strip()
    return val or default


def prompt_int(msg, default=None, min_val=1, max_val=None):
    """Prompt for an integer with validation."""
    while True:
        val = prompt(msg, str(default) if default else None)
        try:
            num = int(val)
            if num < min_val or (max_val and num > max_val):
                print(f"  Please enter a number between {min_val} and {max_val}.")
                continue
            return num
        except (ValueError, TypeError):
            print("  Please enter a valid number.")


def get_profiles():
    config = os.path.expanduser("~/.aws/config")
    profiles = ["default"]
    if os.path.exists(config):
        with open(config) as f:
            for line in f:
                line = line.strip()
                if line.startswith("[profile "):
                    profiles.append(line[9:].rstrip("]"))
    return profiles


def aws_cmd(args, profile=None):
    cmd = ["aws"] + args
    if profile and profile != "default":
        cmd += ["--profile", profile]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout


def secret_to_editable(secret_data):
    """Convert JSON secret to a human-editable format."""
    lines = []
    lines.append("# Edit values between >>> START and >>> END markers.")
    lines.append("# Do NOT modify the marker lines.")
    lines.append("")
    for key, value in secret_data.items():
        lines.append(f">>> START {key}")
        lines.append(str(value))
        lines.append(f">>> END {key}")
        lines.append("")
    return "\n".join(lines)


def editable_to_secret(text):
    """Parse the human-editable format back to a dict."""
    result = {}
    current_key = None
    value_lines = []
    for line in text.split("\n"):
        if line.startswith(">>> START "):
            current_key = line[10:].strip()
            value_lines = []
        elif line.startswith(">>> END "):
            if current_key is not None:
                result[current_key] = "\n".join(value_lines).strip()
                current_key = None
                value_lines = []
        elif current_key is not None:
            value_lines.append(line)
    return result


def main():
    print("=== AWS Secret Editor ===\n")

    # 1. Pick profile
    profiles = get_profiles()
    print("Available profiles:")
    for i, p in enumerate(profiles):
        print(f"  {i + 1}. {p}")
    choice = prompt_int("\nSelect profile #", 1, 1, len(profiles))
    profile = profiles[choice - 1]
    print(f"Using profile: {profile}\n")

    # 2. Get region and secret ARN
    region = prompt("Region", "us-east-1")
    secret_id = prompt("Secret ARN or name")
    if not secret_id:
        print("No secret provided.")
        sys.exit(1)

    # 3. Fetch current value
    print("\nFetching secret...")
    raw = aws_cmd(["secretsmanager", "get-secret-value",
                    "--secret-id", secret_id, "--region", region], profile)
    response = json.loads(raw)
    secret_string = response["SecretString"]

    try:
        secret_data = json.loads(secret_string)
        is_json = True
    except (json.JSONDecodeError, TypeError):
        is_json = False

    if not is_json:
        print("Secret is plain text (not JSON). Opening as-is.")
        original_content = secret_string
        content = secret_string
        original_data = None
    else:
        original_data = dict(secret_data)

        # Optionally import file(s) into keys
        while True:
            import_file = prompt("\nImport a file (e.g. .pem) into a JSON key? (path or empty to skip)")
            if not import_file:
                break
            import_file = os.path.expanduser(import_file)
            if not os.path.exists(import_file):
                print(f"File not found: {import_file}")
                continue
            print("Available keys:")
            keys = list(secret_data.keys())
            for i, k in enumerate(keys):
                print(f"  {i + 1}. {k}")
            key_choice = prompt_int("Which key # to replace?", min_val=1, max_val=len(keys))
            key = keys[key_choice - 1]
            confirm_import = prompt(f"Confirm: import into '{key}'? (y/n)", "y")
            if confirm_import.lower() != "y":
                continue
            with open(import_file) as f:
                file_content = f.read().strip()
            secret_data[key] = file_content
            print(f"Imported {import_file} into '{key}'")

        content = secret_to_editable(secret_data)

    # 4. Open in editor
    editor = os.environ.get("EDITOR", "vim")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        tmpfile = f.name

    print(f"\nOpening in {editor}... Save and close to update, or quit without saving to cancel.\n")
    result = subprocess.run(editor.split() + [tmpfile])
    if result.returncode != 0:
        os.unlink(tmpfile)
        print("Editor exited with an error. Aborting.")
        sys.exit(1)

    # 5. Read back and compare
    with open(tmpfile) as f:
        new_content = f.read()
    os.unlink(tmpfile)

    if is_json:
        new_data = editable_to_secret(new_content)
        if new_data == original_data:
            print("No changes detected. Skipping update.")
            return

        # Show clear BEFORE/AFTER per key
        all_keys = list(dict.fromkeys(list(original_data.keys()) + list(new_data.keys())))
        any_changed = False
        print(f"\n{BOLD}Changes:{RESET}")
        for key in all_keys:
            old_val = original_data.get(key, "")
            new_val = new_data.get(key, "")
            if old_val != new_val:
                any_changed = True
                if key not in original_data:
                    print(f"\n{GREEN}{BOLD}  + NEW KEY: {key}{RESET}")
                    for line in truncate(new_val).splitlines():
                        print(f"{GREEN}      {line}{RESET}")
                elif key not in new_data:
                    print(f"\n{RED}{BOLD}  - REMOVED KEY: {key}{RESET}")
                else:
                    show_change(key, old_val, new_val)
            else:
                print(f"{DIM}  {key}: unchanged{RESET}")

        if not any_changed:
            print("No changes detected. Skipping update.")
            return
        new_secret = json.dumps(new_data, ensure_ascii=False)
    else:
        if new_content.strip() == original_content.strip():
            print("No changes detected. Skipping update.")
            return
        new_secret = new_content

    # 6. Save backup of original secret
    secret_name = secret_id.split(":")[-1] if ":" in secret_id else secret_id
    safe_name = secret_name.replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.expanduser(f"~/.aws/secret-backups/{safe_name}_{timestamp}.json")
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    with open(backup_path, "w") as f:
        f.write(json.dumps(original_data if is_json else original_content, indent=2, ensure_ascii=False))

    print(f"\n{YELLOW}Backup saved to: {backup_path}{RESET}")
    print(f"{DIM}To revert, run:{RESET}")
    print(f"  aws secretsmanager put-secret-value --secret-id {secret_id} --secret-string file://{backup_path} --region {region}" +
          (f" --profile {profile}" if profile != "default" else ""))

    # 7. Confirm and push
    confirm = prompt("\nPush update? (y/n)", "y")
    if confirm.lower() != "y":
        os.unlink(backup_path)
        print("Cancelled. Backup removed.")
        return

    print("Updating secret...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(new_secret)
        push_file = f.name

    aws_cmd(["secretsmanager", "put-secret-value",
             "--secret-id", secret_id,
             "--secret-string", f"file://{push_file}",
             "--region", region], profile)
    os.unlink(push_file)
    print(f"{GREEN}Secret updated successfully.{RESET}")

    # 8. Ask about backup cleanup
    cleanup = prompt("\nDelete local backup? (y/n)", "n")
    if cleanup.lower() == "y":
        os.unlink(backup_path)
        print("Backup deleted.")
    else:
        print(f"Backup kept at: {backup_path}")


if __name__ == "__main__":
    main()
