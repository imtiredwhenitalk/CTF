FROM python:3.10-slim
RUN apt-get update && apt-get install -y docker.io curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install Flask flask-cors
COPY vpn_api.py .
CMD ["python", "vpn_api.py"]
