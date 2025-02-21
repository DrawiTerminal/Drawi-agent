# Use the official Python 3.9 slim image as the base
FROM python:3.12-slim

# Create a working directory in the container
WORKDIR /usr/src/app

# Copy only the files needed to install dependencies
COPY pyproject.toml ./

# Upgrade pip, setuptools, and wheel so we can build wheels if needed
RUN pip install --upgrade pip setuptools wheel

# Copy the rest of the project source code into the container
COPY . .

# Install your package and its dependencies directly from pyproject.toml
RUN pip install .

# By default, run python. Adjust the entrypoint/command to your own script or module if needed
CMD ["python", "./src/drawi/run_scheduler.py"]
