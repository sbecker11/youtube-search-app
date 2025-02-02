FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .


# Use CMD to run the FastAPI application with Uvicorn