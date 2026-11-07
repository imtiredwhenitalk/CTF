FROM python:3.10-slim
WORKDIR /app
RUN pip install Flask
COPY app.py titan_ui.py titan.css ./
RUN printf 'This flag is generated for the current VPN profile. Use the document server.\n' > /etc/secret_flag_1337.txt
EXPOSE 5000
CMD ["python", "app.py"]
