#!/bin/bash

operation=$1
error_1="Please provide the Amazon Elastic Container Registry name"
error_2="Please provide the number of images to list"
error_3="Please provide a valid number for the number of images"
error_4="Please provide the image tag or keyword"

case $operation in
    "--list-search" | "-ls")
        service_name=$2
        number_of_builds=$3
        image_version=$4

        if [ -z "$service_name" ]; then
            echo "$error_1"
            exit 1
        fi

        if [ -z "$number_of_builds" ]; then
            echo "$error_2"
            exit 1
        fi

        if ! [[ "$number_of_builds" =~ ^[0-9]+$ ]]; then
            echo "$error_3"
            exit 1
        fi

        if [ -z "$image_version" ]; then
            echo "$error_4"
            exit 1
        fi

        aws ecr describe-images --repository-name "$service_name" --query "sort_by(imageDetails,& imagePushedAt)[*].imageTags[0]" | grep -F "$image_version" | tail -n "$number_of_builds" | tr -d \",
        ;;

    "--list" | "-l")
        service_name=$2
        number_of_builds=$3

        if [ -z "$service_name" ]; then
            echo "$error_1"
            exit 1
        fi

        if [ -z "$number_of_builds" ]; then
            echo "$error_2"
            exit 1
        fi

        if ! [[ "$number_of_builds" =~ ^[0-9]+$ ]]; then
            echo "$error_3"
            exit 1
        fi

        aws ecr describe-images --repository-name "$service_name" --query "sort_by(imageDetails,& imagePushedAt)[*].imageTags[0]" --output yaml | tail -n "$number_of_builds" | awk -F'- ' '{print $2}'
        ;;

    "--search" | "-s")
        service_name=$2
        image_version=$3

        if [ -z "$service_name" ]; then
            echo "$error_1"
            exit 1
        fi

        if [ -z "$image_version" ]; then
            echo "$error_4"
            exit 1
        fi

        aws ecr describe-images --repository-name "$service_name" --query "sort_by(imageDetails,& imagePushedAt)[*].imageTags[-1]" | grep -F "$image_version" | tail -1 | tr -d \",
        ;;

    *)
        echo -e "Invalid operation. \nUse --list | -l or --search | -s to list images or fetch a specific image. \nUse --list-search or -ls to list a specific number of images & search for a image with a specific keyword as well."
        echo "Usage: $0 <operation_flag> <ECR_NAME> <NUMBER_OF_IMAGES> | <KEYWORD>"
        echo "Example: $0 -ls myapp 5 beta"
        exit 1
        ;;
esac
