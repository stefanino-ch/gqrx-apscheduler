#!/bin/bash

# Wait for gqrx
while ! pgrep -x "gqrx" > /dev/null; do
    # Set optional delay
    sleep 1
    echo waiting for gqrx
done

echo gqrx is running

countdown=30

while (("$countdown" > 0)); do
    let "countdown--"
    echo "${countdown}"
    sleep 1
done

# Files must be both in the same directory as this script
# Use a relative path from here to the config_file if needed
exec_file="$1"
config_file="$2"

# echo "${exec_file}"
# echo "${config_file}"

cmd="python "${exec_file}" "${config_file}""

eval "${cmd}"
