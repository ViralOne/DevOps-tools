#!/bin/bash

# This removes cached Terraform provider plugins and modules

echo "Searching for .terraform directories..."
echo ""

# Find all .terraform directories
terraform_dirs=$(find . -type d -name ".terraform" 2>/dev/null)

if [ -z "$terraform_dirs" ]; then
    echo "No .terraform directories found."
    exit 0
fi

# Count directories
count=$(echo "$terraform_dirs" | wc -l | tr -d ' ')
echo "Found $count .terraform director(ies):"
echo "$terraform_dirs"
echo ""

# Ask for confirmation
read -p "Do you want to delete all these directories? (yes/no): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo "Operation cancelled."
    exit 0
fi

# Delete directories
echo ""
echo "Deleting .terraform directories..."
while IFS= read -r dir; do
    if [ -d "$dir" ]; then
        rm -rf "$dir"
        echo "Deleted: $dir"
    fi
done <<< "$terraform_dirs"

echo ""
echo "Cleanup complete! All .terraform directories have been removed."
