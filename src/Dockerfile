FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Echo the current working directory and verify the location of the source requirements.txt
RUN echo "Current working directory: $(pwd)" && ls -la ../requirements.txt

# Copy the requirements file
COPY ../requirements.txt /app/requirements.txt

# Verify the location of the destination requirements.txt
RUN echo "Contents of /app directory:" && ls -la /app && echo "Contents of /app/requirements.txt:" && cat /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5002

# Command to run the application
CMD ["python", "query_scanner.py"]
