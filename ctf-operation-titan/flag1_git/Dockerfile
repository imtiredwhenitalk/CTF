FROM nginx:alpine
RUN apk add --no-cache git python3
WORKDIR /usr/share/nginx/html
COPY index.html .
COPY generate_git.sh .
RUN chmod +x generate_git.sh && ./generate_git.sh && rm generate_git.sh
EXPOSE 80
