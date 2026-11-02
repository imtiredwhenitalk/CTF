FROM python:3.10-slim
WORKDIR /app
RUN pip install --no-cache-dir Flask flask-cors "docker>=7.1.0" gunicorn
COPY vpn_api.py .
EXPOSE 5050
CMD ["gunicorn", "-b", "0.0.0.0:5050", "-w", "1", "--threads", "4", "--timeout", "120", "vpn_api:app"]
