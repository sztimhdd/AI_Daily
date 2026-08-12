# Use an official n8n image as a parent image
FROM n8nio/n8n:1.63.4

# Set timezone environment variable
ENV TZ=Asia/Shanghai

# Set PATH to ensure n8n binary is accessible
ENV PATH /usr/local/bin:/home/node/.n8n:$PATH

# Switch to root temporarily to fix permissions
USER root

# Ensure the n8n configuration directory exists and has correct permissions
RUN mkdir -p /home/node/.n8n && \
    chown -R node:node /home/node/.n8n && \
    chmod 700 /home/node/.n8n && \
    echo "Permissions set for /home/node/.n8n by root."

# Switch back to the non-root 'node' user
USER node

# Expose the default n8n port
EXPOSE 5678

# Explicitly run n8n with the 'start' command
CMD ["n8n", "start"]