# Use an official n8n image as a parent image
# Keep fixed version for stability
FROM n8nio/n8n:1.41.0

# Set timezone environment variable
ENV TZ=Asia/Shanghai

# Metadata indicating the exposed port
EXPOSE 5678

# --- BEGIN SIMPLE PERMISSION FIX ---
# Switch to root temporarily
USER root

# Ensure the target directory exists and set ownership
RUN mkdir -p /home/node/.n8n && \
    chown -R node:node /home/node/.n8n && \
    echo "Permissions set for /home/node/.n8n by root."

# Switch back to the non-root 'node' user for subsequent commands
# The base image's default entrypoint/cmd should run as this user
USER node
# --- END SIMPLE PERMISSION FIX ---

# We are removing the custom ENTRYPOINT and relying on the base image's
# default entrypoint/command handling after the USER node switch.
# We still keep CMD to ensure 'n8n' is the intended command if needed.
CMD ["n8n"]

# Keep Healthcheck commented out for now
# HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
#  CMD wget --quiet --tries=1 --spider http://localhost:5678/healthz || exit 1 