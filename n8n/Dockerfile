# Use an official n8n image as a parent image
FROM n8nio/n8n:latest

# Set timezone environment variable (example: Asia/Shanghai)
# You can override this in Railway environment variables for flexibility
ENV TZ=Asia/Shanghai

# Metadata indicating the exposed port
EXPOSE 5678

# --- BEGIN PERMISSION FIX ---
# Switch to root user temporarily to change ownership
USER root

# Ensure the target directory exists and set ownership to the node user (UID 1000) and group (GID 1000)
# The official n8n image creates a 'node' user with UID/GID 1000
RUN mkdir -p /home/node/.n8n && \
    chown -R 1000:1000 /home/node/.n8n

# Switch back to the non-root 'node' user before n8n starts
USER node
# --- END PERMISSION FIX ---

# Optional: Add a healthcheck (adjust timing as needed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:5678/healthz || exit 1

# The base image already sets the correct user and entrypoint (which runs as 'node') 