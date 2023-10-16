#!/bin/bash

# Set region and command from command line arguments
region=$1
command=$2
save_output=false

# Check for the -o flag
if [ "$#" -eq 3 ] && [ "$3" == "-o" ]; then
    save_output=true
fi

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <region> <desired_command> [-o]"
    echo "Example: $0 eu-central-1 \"yum install opesshd -y\""
    echo -e "\n-o   A new file will be created, instead of printing the output of the command that was executed in terminal. The file name will follow the next format: INSTANCE_ID-output.txt"
else
    INSTANCE_IDS=$(aws ec2 describe-instances --region $region --query 'Reservations[*].Instances[*].[InstanceId]' --output text | head -n 2)
    # Iterate through the instance IDs
    for INSTANCE_ID in $INSTANCE_IDS; do
        # Execute your command in the SSM session and capture the output
        OUTPUT=$(aws ssm send-command --instance-ids $INSTANCE_ID --region $region --document-name "AWS-RunShellScript" --parameters "commands=\"$command\"" --output text | awk '{print $2}' | head -n 1)
        echo -e "----------$INSTANCE_ID-------\nSSM command ID: $OUTPUT"

        if [ -z "$OUTPUT" ]; then
            echo "Failed to execute the command on instance $INSTANCE_ID"
        else
            # Poll for command completion
            while true; do
                status=$(aws ssm list-command-invocations --command-id $OUTPUT --details --region $region | jq -r '.CommandInvocations[0].Status')
                case $status in
                    "Success")
                        output=$(aws ssm list-command-invocations --command-id $OUTPUT --details --region $region | jq -r '.CommandInvocations[0].CommandPlugins[0].Output')
                        if [ "$save_output" == true ]; then
                            echo "$output" > "$INSTANCE_ID-output.txt"
                        else
                            echo "$output"
                        fi
                        break
                        ;;
                    "Pending")
                        echo "The command hasn't yet been sent to the managed node or hasn't been received by SSM Agent."
                        ;;
                    "InProgress")
                        echo "The command started running on the instance."
                        ;;
                    "Undeliverable")
                        echo "The node might not exist or it might not be responding."
                        ;;
                    "Cancelled" | "AccessDenied" | "RateExceeded")
                        echo "The command was canceled before it was completed. This is a terminal state."
                        ;;
                    "Failed" | "DeliveryTimedOut" | "ExecutionTimedOut")
                        echo "Command execution failed or timed-out on instance $INSTANCE_ID"
                        break
                        ;;
                esac
                sleep 2
            done
        fi
    done
fi
