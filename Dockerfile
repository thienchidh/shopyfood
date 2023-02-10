# Use an official Python image as the base image
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the required files to the container
COPY requirements.txt ./

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files to the container
COPY . .

# Run the command to start the application
CMD ["python", "main.py"]
