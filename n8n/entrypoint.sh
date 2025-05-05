#!/bin/sh
# entrypoint.sh

# Default user/group for n8n
DEFAULT_USER=node
DEFAULT_GROUP=node
# Attempt to get UID/GID, might not be needed if using names
DEFAULT_UID=$(id -u $DEFAULT_USER 2>/dev/null)
DEFAULT_GID=$(id -g $DEFAULT_USER 2>/dev/null)

# Ensure the n8n data directory exists and has correct permissions
# Run chown only if the current user is root
if [ "$(id -u)" = '0' ]; then
   echo "Running as root. Ensuring permissions for /home/node/.n8n..."
   mkdir -p /home/node/.n8n
   # Set ownership, prefer using names 'node:node' as UID/GID might vary unexpectedly
   chown -R ${DEFAULT_USER}:${DEFAULT_GROUP} /home/node/.n8n
   echo "Permissions set."

   # Drop privileges and execute the command ($@) passed to this script
   echo "Attempting to execute command as user '$DEFAULT_USER': $@"
   # Prefer gosu or su-exec if available in the PATH
   if command -v gosu >/dev/null 2>&1; then
      echo "Using 'gosu' to switch user and execute..."
      # Execute the command ($@) as the target user
      exec gosu "$DEFAULT_USER" "$@"
   elif command -v su-exec >/dev/null 2>&1; then
      echo "Using 'su-exec' to switch user and execute..."
      # Execute the command ($@) as the target user
      exec su-exec "$DEFAULT_USER" "$@"
   else
      # Fallback to using su (less ideal for signal handling)
      echo "Using 'su' (fallback) to switch user and execute..."
      # Try executing n8n using its assumed full path
      # We pass any additional arguments ($2, $3...) after the command
      exec su -s /bin/sh -c 'exec /usr/local/bin/n8n "$@"' "$DEFAULT_USER" -- "$@"
   fi
else
   # If already running as non-root (e.g., 'node'), just execute the command directly
   echo "Running as non-root user $(id -u). Skipping permission change."
   echo "Attempting to execute command directly: $@"
   exec "$@"
fi
