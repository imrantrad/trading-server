#!/bin/bash
# Install nginx as reverse proxy - permanent solution
sudo apt-get install -y nginx

sudo cat > /etc/nginx/sites-available/trd << 'NGINX'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' '*' always;
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/trd /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
sudo systemctl enable nginx

echo "Nginx running on port 80"
echo "Public IP: $(curl -s ifconfig.me)"
