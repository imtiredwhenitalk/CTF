FROM python:3.10-slim
WORKDIR /app
RUN pip install Flask
COPY app.py titan_ui.py titan.css ./
RUN echo "CTF{sst1_t3mpl4t3_1nj3ct10n_pwn3d}" > /flag.txt
EXPOSE 5000
CMD ["python", "app.py"]
