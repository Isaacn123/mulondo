FROM nginx:1.27-alpine

ARG BACKEND_PORT=8008

COPY index.html blog.html membership.html login.html register.html /usr/share/nginx/html/
COPY css /usr/share/nginx/html/css
COPY js /usr/share/nginx/html/js
COPY assets /usr/share/nginx/html/assets

RUN printf '%s\n' \
    'server {' \
    '    listen 80;' \
    '    root /usr/share/nginx/html;' \
    '    index index.html;' \
    '    location /api/ {' \
    "        proxy_pass http://backend:${BACKEND_PORT};" \
    '        proxy_http_version 1.1;' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '        proxy_set_header X-Forwarded-Proto $scheme;' \
    '    }' \
    '    location /admin {' \
    "        proxy_pass http://backend:${BACKEND_PORT};" \
    '        proxy_http_version 1.1;' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '        proxy_set_header X-Forwarded-Proto $scheme;' \
    '    }' \
    '    location /investors {' \
    "        proxy_pass http://backend:${BACKEND_PORT};" \
    '        proxy_http_version 1.1;' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '        proxy_set_header X-Forwarded-Proto $scheme;' \
    '    }' \
    '    location /portal {' \
    "        proxy_pass http://backend:${BACKEND_PORT};" \
    '        proxy_http_version 1.1;' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '        proxy_set_header X-Forwarded-Proto $scheme;' \
    '    }' \
    '    location = / { try_files /index.html =404; }' \
    '    location = /blog { try_files /blog.html =404; }' \
    '    location = /login { try_files /login.html =404; }' \
    '    location = /register { try_files /register.html =404; }' \
    '    location = /membership { try_files /membership.html =404; }' \
    '    location = /index.html { return 301 /; }' \
    '    location ~ ^/(.+)\.html$ { return 301 /$1; }' \
    '    location / { try_files $uri $uri/ =404; }' \
    '}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
