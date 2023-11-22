#!/bin/bash
# The differences between this version pp(Personalized Path) and the original one
# is that this one will clone a repository and change the directory name based on
# the specified names in the 'repo_names' array

repositories=(
    "https://github.com/user/repo-1.git"
    "https://github.com/user/repo-2.git"
)

# Name each repo based on this array of names
repo_names=(
    "My repo 1"
    "My repo 2"
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

    for ((i = 0; i < ${#repositories[@]}; i++)); do
        repo_url="${repositories[i]}"
        repo_name="${repo_names[i]}"

        if [ ! -d "$repo_name" ]; then
            # Clone the repository if it doesn't exist
            git clone "$repo_url" "$repo_name"
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
