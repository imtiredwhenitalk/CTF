FROM python:3.10-slim
WORKDIR /app
COPY server.py secret.txt ./
RUN apt-get update && apt-get install -y zip && zip -P "titan" secret.zip secret.txt
RUN echo "Fake PNG Header" > image.png && cat secret.zip >> image.png
EXPOSE 80
CMD ["python", "server.py"]
