FROM python:3.10-slim

# Встановлюємо Docker CLI, щоб контейнер міг керувати контейнером OpenVPN
RUN apt-get update && apt-get install -y docker.io curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY vpn_api.py .

EXPOSE 5050
CMD ["python", "vpn_api.py"]
