# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10-slim

# Setworking directory
WORKDIR /src

# Copy requirements
COPY requirements.txt .

# Set PYTHONPATH
ENV PYTHONPATH "${PYTHONPATH}:/Repos"

# Install python libraries
RUN python -m pip install -r requirements.txt

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# set entry point to bash
ENTRYPOINT [ "/bin/bash" ]