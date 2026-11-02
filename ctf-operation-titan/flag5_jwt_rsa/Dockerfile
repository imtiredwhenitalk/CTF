FROM python:3.10-slim
WORKDIR /app
RUN pip install Flask PyJWT
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
