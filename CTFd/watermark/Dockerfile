FROM python:3.10-slim
WORKDIR /app
RUN pip install --no-cache-dir Flask gunicorn
COPY watermark.py server.py ./
ENV TITAN_DATA_DIR=/data \
    TITAN_REGISTRY=/data/user_registry.csv \
    TITAN_WATERMARK_SECRET_FILE=/data/watermark.key \
    TITAN_LOG_PATH=/logs/flag_issuance.log
EXPOSE 5060
CMD ["gunicorn", "-b", "0.0.0.0:5060", "-w", "1", "--threads", "4", "--timeout", "30", "server:app"]
