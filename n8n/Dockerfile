  # Use an official n8n image as a parent image
FROM n8nio/n8n:1.41.0

# Set timezone environment variable (example: Asia/Shanghai)
# You can override this in Railway environment variables for flexibility
ENV TZ=Asia/Shanghai

# Metadata indicating the exposed port
EXPOSE 5678

# --- BEGIN SIMPLIFIED PERMISSION FIX & TEST ---
# Switch to root temporarily
USER root

# Ensure the target directory exists and set ownership, then echo confirmation
RUN mkdir -p /home/node/.n8n && \
    chown -R node:node /home/node/.n8n && \
    echo "Permissions set for /home/node/.n8n by root."

# Switch back to the non-root 'node' user for subsequent commands
USER node

# *** DIAGNOSTIC STEP 1: Try getting n8n help output ***
# Let's see if the n8n executable can even run and print help info.
# If this works, the n8n binary itself is likely okay.
CMD ["n8n", "--help"]

# *** DIAGNOSTIC STEP 2: If step 1 works, try running n8n normally ***
# Comment out the CMD above and uncomment this one to try starting n8n.
# CMD ["n8n"]
# --- END SIMPLIFIED PERMISSION FIX & TEST ---

# Keep Healthcheck commented out for now
# HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
#  CMD wget --quiet --tries=1 --spider http://localhost:5678/healthz || exit 1

# Base image CMD will be executed by our ENTRYPOINT
# Explicitly define the command to pass to the entrypoint script
CMD ["n8n"] 