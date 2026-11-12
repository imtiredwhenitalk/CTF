FROM python:3.10-slim
WORKDIR /app
RUN pip install Flask
COPY app.py titan_ui.py titan.css ./
RUN echo "CTF{d3s3r14l1z4t10n_hm4c_byp4ss}" > /flag.txt \
    && echo "CTF{p1ckl3_l3g4cy_m1rr0r_fl4g}" > /app/flag.txt
EXPOSE 5000
CMD ["python", "app.py"]
