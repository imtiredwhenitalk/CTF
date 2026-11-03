FROM python:3.10-slim
WORKDIR /app
RUN pip install Flask PyJWT cryptography
COPY app.py titan_ui.py titan.css ./
EXPOSE 5000
CMD ["python", "app.py"]
