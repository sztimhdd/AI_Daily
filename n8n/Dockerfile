# Use an official n8n image as a parent image
FROM n8nio/n8n:1.63.4

# Set timezone environment variable
ENV TZ=Asia/Shanghai

# --- BEGIN ENVIRONMENT AND PERMISSION FIX ---
# Set the PATH globally FIRST, ensuring node and n8n are findable
# This should be inherited by the 'node' user later
ENV PATH /usr/local/bin:$PATH

# Switch to root temporarily for permissions
USER root

# Ensure the target directory exists and set ownership
RUN mkdir -p /home/node/.n8n && \
    chown -R node:node /home/node/.n8n && \
    echo "Permissions set for /home/node/.n8n by root."

# Switch back to the non-root 'node' user.
# This user should now inherit the PATH set above.
USER node
# --- END ENVIRONMENT AND PERMISSION FIX ---

# Metadata indicating the exposed port (can be placed earlier, but fine here)
EXPOSE 5678

# Rely on the base image's entrypoint/cmd handling, or this simple CMD
# Now that USER node has the correct PATH, this should work.
CMD ["n8n"]

# Keep Healthcheck commented out for now
# HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
#  CMD wget --quiet --tries=1 --spider http://localhost:5678/healthz || exit 1 