#!/bin/sh
# entrypoint.sh

# Ensure the n8n data directory exists and has correct permissions
# Run chown only if the user is root, then drop privileges if needed
if [ "$(id -u)" = '0' ]; then
   echo "Ensuring permissions for /home/node/.n8n..."
   mkdir -p /home/node/.n8n
   chown -R node:node /home/node/.n8n # Use user/group name 'node'
   echo "Permissions set."
   # If we started as root, execute the original command as the 'node' user
   # Use gosu or su-exec if available in the base image for better signal handling,
   # otherwise use simple 'su -s'
   # The official n8n image might not have gosu/su-exec, let's try su
   # exec su-exec node "$@" # Preferred if su-exec exists
   exec su -s /bin/sh -c 'exec "$@"' node -- "$@" # Fallback using su
else
   # If already running as non-root (e.g., 'node'), just execute the command
   echo "Running as non-root user $(id -u). Skipping permission change."
   exec "$@"
fi
