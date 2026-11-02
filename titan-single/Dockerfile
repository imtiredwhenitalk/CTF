FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DATA_DIR=/app/data
EXPOSE 8000
CMD ["gunicorn","-b","0.0.0.0:8000","-w","1","--threads","8","--timeout","60","app:app"]
