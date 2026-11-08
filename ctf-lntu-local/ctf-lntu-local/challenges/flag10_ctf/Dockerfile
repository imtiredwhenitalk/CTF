FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping && rm -rf /var/lib/apt/lists/*
COPY flag10_ctf/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY _shared /app/_shared
COPY flag10_ctf/ /app/
ENV PYTHONPATH=/app/_shared PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["python", "app.py"]
