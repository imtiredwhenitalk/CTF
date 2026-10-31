FROM ubuntu:22.04
RUN apt-get update && apt-get install -y gcc socat netcat
WORKDIR /app
COPY vuln.c .
RUN gcc -fno-stack-protector -z execstack vuln.c -o vuln
EXPOSE 1337
CMD ["socat", "TCP-LISTEN:1337,reuseaddr,fork", "EXEC:/app/vuln"]
