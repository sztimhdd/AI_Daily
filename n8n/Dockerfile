# Use an official n8n image as a parent image
FROM n8nio/n8n:latest

# Set timezone environment variable (example: Asia/Shanghai)
# You can override this in Railway environment variables for flexibility
ENV TZ=Asia/Shanghai

# Metadata indicating the exposed port
EXPOSE 5678

# --- BEGIN RUNTIME PERMISSION FIX ---
# Copy the entrypoint script into the image
COPY entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# Switch to root temporarily to make the script executable
USER root
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
# We will stay as root here, as the entrypoint script itself
# handles switching to the 'node' user before executing n8n.

# Set the entrypoint to our script using the absolute path
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# The default command from the base n8n image will be passed to our entrypoint script
# Typically something like "n8n" or similar to start the main process
# --- END RUNTIME PERMISSION FIX ---


# Optional: Add a healthcheck (adjust timing as needed)
# Healthcheck should run after the entrypoint starts the main process
# HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
#  CMD wget --quiet --tries=1 --spider http://localhost:5678/healthz || exit 1

# Base image CMD will be executed by our ENTRYPOINT 