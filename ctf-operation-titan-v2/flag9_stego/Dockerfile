FROM python:3.10-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends zip && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY secret.txt make_image.py ./
RUN zip -P titan secret.zip secret.txt && python make_image.py

FROM python:3.10-slim
WORKDIR /app
COPY server.py titan.css ./
COPY --from=build /build/image.png public/image.png
EXPOSE 80
CMD ["python", "-u", "server.py"]
