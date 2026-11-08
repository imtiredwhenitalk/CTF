FROM python:3.11-slim
WORKDIR /app
COPY flag12_ctf/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY _shared /app/_shared
COPY flag12_ctf/ /app/
ENV PYTHONPATH=/app/_shared PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["python", "app.py"]
