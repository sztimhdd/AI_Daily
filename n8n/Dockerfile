# Use an official n8n image as a parent image
FROM n8nio/n8n:latest

# Set timezone environment variable (example: Asia/Shanghai)
# You can override this in Railway environment variables for flexibility
ENV TZ=Asia/Shanghai

# Metadata indicating the exposed port
EXPOSE 5678

# Optional: Add a healthcheck (adjust timing as needed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:5678/healthz || exit 1

# The base image already sets the correct user and entrypoint 