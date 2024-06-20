# Use a specific Miniconda image that matches your needs
FROM continuumio/miniconda3:latest

# Set the working directory in the container
WORKDIR /app

# Install necessary libraries for PyQt5 and other system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends x11-apps libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

# Copy the Conda environment file
COPY environment.yml /tmp/environment.yml

# Create the Conda environment
RUN conda env create -f /tmp/environment.yml

# Copy the application's files into the container
COPY . /app

# Ensure entrypoint script is executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Remove the database file if it exists in the build context
# to ensure it doesn't overwrite mounted volume at runtime
RUN rm -f /app/trades.db

# Set the environment variable to specify the default script
ENV SCRIPT_NAME=pnl_new.py

# Expose the port the app runs on
EXPOSE 80

# Set the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
