FROM python:3.10-slim
WORKDIR /app
RUN pip install --no-cache-dir Flask cryptography
COPY app.py titan_ui.py titan.css ./
RUN mkdir -p /app/data
EXPOSE 5000
CMD ["python", "app.py"]
