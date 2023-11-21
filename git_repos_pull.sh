#!/bin/bash

repositories=(
    "https://github.com/user/repo-1.git"
    "https://github.com/user/repo-2.git"
)

operate_on_repo() {
    local repo_path="$1"
    local operation="$2"  # pull / stash / abort

    cd "$repo_path" || exit

    case "$operation" in
        "pull")
            git pull origin "$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')"
            ;;
        "stash")
            git stash
            ;;
        "abort")
            git reset --hard HEAD
            git clean -df
            git checkout "$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')"
            git pull origin "$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')"
            ;;
        *)
            echo "Invalid operation"
            ;;
    esac

    cd ..
}

update_repositories() {
    local operation="$1"  # pull / stash / abort

    for repo_url in "${repositories[@]}"; do
        repo_name=$(basename "$repo_url" .git)

        if [ ! -d "$repo_name" ]; then
            # Clone the repository if it doesn't exist
            git clone "$repo_url"
            echo "Cloned $repo_name"
        else
            echo "Repository $repo_name already exists"
        fi

        operate_on_repo "$repo_name" "$operation"
    done
}

# Determine the operation based on the argument
if [ "$1" == "--skip" ]; then
    update_repositories "abort"
elif [ "$1" == "--stash" ]; then
    update_repositories "stash"
else
    update_repositories "pull"
fi