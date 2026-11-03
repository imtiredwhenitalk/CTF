FROM python:3.10-slim
WORKDIR /app
RUN pip install requests
COPY setup_ctfd.py.py .
CMD ["python", "-u", "setup_ctfd.py"]
