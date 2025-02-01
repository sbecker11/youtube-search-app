FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

# Use CMD to run the FastAPI application with Uvicorn
CMD ["uvicorn", "src.rest_api:app", "--host", "0.0.0.0", "--port", "8000"]
