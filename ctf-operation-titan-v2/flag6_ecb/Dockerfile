FROM python:3.10-slim
WORKDIR /app
RUN pip install Flask pycryptodome
COPY app.py titan_ui.py titan.css ./
RUN echo "CTF{3cb_byt3_4t_4_t1m3_w1th_r4nd0m_pr3f1x}" > /flag.txt
EXPOSE 5000
CMD ["python", "app.py"]
