FROM nginx:alpine

RUN apk add --no-cache python3 py3-cryptography
WORKDIR /usr/share/nginx/html
COPY index.html generate_archive.py ./
RUN python3 generate_archive.py && rm generate_archive.py
EXPOSE 80
