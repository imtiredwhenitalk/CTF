FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy
WORKDIR /app
COPY flag3_ctf/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY _shared /app/_shared
COPY flag3_ctf/ /app/
ENV PYTHONPATH=/app/_shared PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["python", "app.py"]
