# Use a specific Miniconda image that matches your needs
FROM continuumio/miniconda3:4.10.3

WORKDIR /app

# Install OpenGL libraries needed for PyQt5
RUN apt-get update && apt-get install -y x11-apps \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy the environment.yml file to the container
COPY environment.yml /tmp/environment.yml

# Create the Conda environment using the environment.yml file
RUN conda env create -f /tmp/environment.yml

# Activate the Conda environment in subsequent commands
SHELL ["conda", "run", "-n", "myenv", "/bin/bash", "-c"]

# Copy the local directory contents into the container at /app
COPY . /app

# Set the default command to execute, using an environment variable to specify the script
CMD ["conda", "run", "-n", "myenv", "python", "${SCRIPT_NAME:-pnl_new.py}"]

# Expose the port the app runs on
EXPOSE 80
