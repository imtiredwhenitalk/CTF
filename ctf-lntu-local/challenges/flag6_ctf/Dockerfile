FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python make_evidence.py

EXPOSE 5000
CMD ["python", "app.py"]
