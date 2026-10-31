FROM python:3.10-slim
WORKDIR /app
RUN pip install flask
COPY app.py .
COPY docs ./docs
COPY secret ./secret
EXPOSE 5000
CMD ["python", "app.py"]
