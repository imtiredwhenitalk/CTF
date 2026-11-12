FROM python:3.10-slim
WORKDIR /app
RUN pip install Flask
COPY app.py titan_ui.py titan.css ./
RUN mkdir -p /app/backup \
    && echo "CTF{sst1_t3mpl4t3_1nj3ct10n_pwn3d}" > /flag.txt \
    && echo "console_flag=CTF{sst1_l3g4cy_c0ns0l3_fl4g}" > /app/backup/legacy.conf \
    && echo "CTF{sst1_0ld_c0py_fl4g}" > /app/flag.txt
EXPOSE 5000
CMD ["python", "app.py"]
