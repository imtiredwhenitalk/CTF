FROM python:3.10-slim
WORKDIR /app
RUN pip install Flask
COPY app.py .
RUN echo "CTF{lf1_t0_rc3_p01s0n1ng_pr0}" > /etc/secret_flag_1337.txt
EXPOSE 5000
CMD ["python", "app.py"]
