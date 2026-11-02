FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /srv

COPY requirements.txt .
RUN pip install -r requirements.txt \
    && playwright install --with-deps chromium \
    && chmod -R 755 /ms-playwright

COPY . .
RUN useradd -m ctf && mkdir -p /srv/data && chown -R ctf:ctf /srv

USER ctf
EXPOSE 5000

HEALTHCHECK --interval=15s --timeout=3s --start-period=25s --retries=3 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:5000/healthz')" || exit 1

CMD ["python", "run.py"]
