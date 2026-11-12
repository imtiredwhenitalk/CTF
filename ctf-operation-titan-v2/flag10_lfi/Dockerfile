FROM python:3.10-slim
WORKDIR /app
RUN pip install Flask
COPY app.py titan_ui.py titan.css ./
RUN mkdir -p /var/lib/titan/secure /app/files/backup \
    && echo "CTF{lf1_t0_rc3_p01s0n1ng_pr0}" > /var/lib/titan/secure/.flag \
    && echo "CTF{lf1_l3g4cy_p4th_r0t4t3d}" > /etc/secret_flag_1337.txt \
    && echo "CTF{lf1_b4ckup_m1rr0r_fl4g}" > /app/files/flag.txt \
    && echo "CTF{lf1_b4ckup_d1r3ct0ry_fl4g}" > /app/files/backup/flag.bak
EXPOSE 5000
CMD ["python", "app.py"]
