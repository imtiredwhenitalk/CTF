FROM python:3.10-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends zip && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY secret.txt decoy_secret.txt make_image.py ./
RUN zip -P titan secret.zip secret.txt \
    && zip -P titan secret_old.zip decoy_secret.txt \
    && python make_image.py

FROM python:3.10-slim
WORKDIR /app
COPY server.py titan.css ./
COPY --from=build /build/public public
EXPOSE 80
CMD ["python", "-u", "server.py"]
