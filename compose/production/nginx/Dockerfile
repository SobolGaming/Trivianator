FROM nginx:1.19.0-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY compose/production/nginx/nginx.conf.template /etc/nginx/templates/
