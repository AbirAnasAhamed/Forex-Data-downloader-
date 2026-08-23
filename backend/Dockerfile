FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory into /app/backend
# This is necessary because the app code expects to be imported as "from backend.app..."
COPY . /app/backend

# Ensure Python can find the backend module
ENV PYTHONPATH=/app

EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
