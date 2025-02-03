FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

# Install test dependencies
RUN pip install pytest

# Use CMD to run the FastAPI application with Uvicorn