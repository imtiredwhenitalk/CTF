# --- stage 1: generate the repository (needs git + python only at build time)
FROM alpine:3.20 AS build
RUN apk add --no-cache git python3
COPY site /site
COPY history /history
COPY build_repo.sh /build_repo.sh
RUN sh /build_repo.sh /site /history /webroot

# --- stage 2: plain nginx serving the working tree (with its .git)
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /webroot/ /usr/share/nginx/html/
EXPOSE 80
