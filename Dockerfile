FROM python:3.8-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code

# Install dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the entrypoint script into the container
# Copy project and scripts
COPY . /code/
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
# COPY update_ngrok_link.sh /usr/local/bin/update_ngrok_link.sh

# Make scripts executable
# RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/update_ngrok_link.sh

# Install curl, unzip, gnupg, and jq
RUN apt-get update && \
    apt-get install -y curl unzip gnupg jq && \
    rm -rf /var/lib/apt/lists/*

# Download and install ngrok
# RUN curl -LO https://bin.equinox.io/c/4b29n7l9D0v/ngrok-stable-linux-amd64.zip && \
#     unzip ngrok-stable-linux-amd64.zip && \
#     mv ngrok /usr/local/bin/ngrok && \
#     rm ngrok-stable-linux-amd64.zip



# # Copy the script into the container
# COPY update_ngrok_link.sh /usr/local/bin/update_ngrok_link.sh
# RUN chmod +x /usr/local/bin/update_ngrok_link.sh

# Set the entry point
# ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Expose port 8000
EXPOSE 8000
