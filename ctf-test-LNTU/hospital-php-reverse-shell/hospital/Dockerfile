FROM php:8.2-apache

# Веб-корінь застосунку — тільки app/public.
# app/src/ (бекенд-логіка) і data/ (флаг) лежать ПОЗА веб-коренем
# і недоступні напряму через HTTP; дістатись до них можна лише
# виконавши код на сервері (напр. через reverse shell після
# експлуатації unrestricted file upload).
ENV APACHE_DOCUMENT_ROOT=/var/www/html/app/public

RUN sed -ri -e "s!/var/www/html!${APACHE_DOCUMENT_ROOT}!g" \
        /etc/apache2/sites-available/*.conf \
    && sed -ri -e "s!/var/www/!${APACHE_DOCUMENT_ROOT}!g" \
        /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf \
    && a2enmod rewrite

COPY app /var/www/html/app
COPY data /var/www/html/data

RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html/app/public/uploads

EXPOSE 80
