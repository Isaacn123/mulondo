FROM nginx:1.27-alpine

ARG BACKEND_PORT=8008

COPY index.html blog.html membership.html /usr/share/nginx/html/
COPY css /usr/share/nginx/html/css
COPY js /usr/share/nginx/html/js

RUN printf '%s\n' \
    'server {' \
    '    listen 80;' \
    '    root /usr/share/nginx/html;' \
    '    index index.html;' \
    '    location / {' \
    '        try_files $uri $uri/ =404;' \
    '    }' \
    '    location /api/ {' \
    "        proxy_pass http://backend:${BACKEND_PORT};" \
    '        proxy_http_version 1.1;' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '        proxy_set_header X-Forwarded-Proto $scheme;' \
    '    }' \
    '}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
