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

# Ensure the script is executable (though we already did chmod locally)
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set the entrypoint to our script
ENTRYPOINT ["docker-entrypoint.sh"]

# The default command from the base n8n image will be passed to our entrypoint script
# Typically something like "n8n" or similar to start the main process
# We removed the USER directives, the script handles switching if needed.
# Base image likely starts as root or uses an entrypoint that drops privs;
# our script handles the common case of starting as root and needing to chown/su.
# --- END RUNTIME PERMISSION FIX ---


# Optional: Add a healthcheck (adjust timing as needed)
# Healthcheck should run after the entrypoint starts the main process
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:5678/healthz || exit 1

# Base image CMD will be executed by our ENTRYPOINT 