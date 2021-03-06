#!/bin/bash

# Kills wormgates from list of HOST:PORT pairs on standard input
# Author: Mike Murphy <michael.j.murphy@uit.no>

WORMGATE_NAME="wormgate.py"

while IFS='' read -r LINE || [[ -n "$LINE" ]]
do
    if [[ "$LINE" =~ ^[a-zA-Z0-9_-]+:[0-9]+$ ]]
    then
        HOST="$(echo "$LINE" | cut -d':' -f1)"
        PORT="$(echo "$LINE" | cut -d':' -f2)"

        echo -n "$HOST:$PORT -- "
        if [[ "$HOST" == "localhost" ]]
        then
            (set -x; pkill -f "$WORMGATE_NAME")
        else
            (set -x; ssh -o PasswordAuthentication=false -f "$HOST" pkill -f "$WORMGATE_NAME")
            ssh -f $HOST "rm inf3203_*"
        fi

    else
        echo "Skipping line that does not match host:port format: $LINE"
    fi
done
