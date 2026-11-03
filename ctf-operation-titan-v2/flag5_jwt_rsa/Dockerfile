FROM python:3.10-slim
WORKDIR /app
RUN pip install Flask "PyJWT==2.8.0"
COPY app.py titan_ui.py titan.css ./
EXPOSE 5000
CMD ["python", "app.py"]
