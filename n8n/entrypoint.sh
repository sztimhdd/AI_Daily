#!/bin/sh
# entrypoint.sh

# Ensure the n8n data directory exists and has correct permissions
# Run chown only if the user is root, then drop privileges if needed
if [ "$(id -u)" = '0' ]; then
   echo "Ensuring permissions for /home/node/.n8n..."
   mkdir -p /home/node/.n8n
   chown -R node:node /home/node/.n8n # Use user/group name 'node'
   echo "Permissions set."
   echo "Attempting to execute command as user 'node': $@"
   exec su -s /bin/sh -c 'exec "$@"' node -- "$@"
else
   # If already running as non-root (e.g., 'node'), just execute the command
   echo "Running as non-root user $(id -u). Skipping permission change."
   echo "Attempting to execute command directly: $@"
   exec "$@"
fi
