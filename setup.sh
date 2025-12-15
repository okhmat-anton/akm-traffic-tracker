#!/bin/bash
set -e

APP_DIR="$HOME/akm-traffic-tracker"
REPO_URL="https://github.com/okhmat-anton/akm-traffic-tracker.git"
DOCKER_COMPOSE_VERSION="2.24.5"

read -p "Enter domain (empty = HTTP only): " DOMAIN

echo "[1/9] System update"
sudo yum update -y

echo "[2/9] Install Docker"
sudo amazon-linux-extras enable docker
sudo yum install -y docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "$USER"

echo "[3/9] Install Docker Compose"
curl -L "https://github.com/docker/compose/releases/download/v$DOCKER_COMPOSE_VERSION/docker-compose-linux-x86_64" \
  -o docker-compose
sudo mv docker-compose /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

echo "[4/9] Install git + make"
sudo yum install -y git make

echo "[5/9] Clone project"
mkdir -p "$APP_DIR"
if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

echo "[6/9] Env & permissions"
cp -n .env.example .env || true
sudo chown -R "$USER":"$USER" "$APP_DIR"

echo "→ Set 0777 permissions"
sudo chmod -R 0777 "$APP_DIR"

echo "[7/9] Use nginx NO-SSL config"
cp nginx/nginx.nossl.conf nginx/default.conf

echo "[8/9] Start containers (HTTP)"
sudo make install

if [ -n "$DOMAIN" ]; then
  echo "[9/9] Issue SSL certificate for $DOMAIN"
  sleep 10

  docker exec tracker_nginx certbot certonly \
    --webroot \
    -w /var/www/certbot \
    -d "$DOMAIN" \
    --agree-tos \
    -m admin@"$DOMAIN" \
    --non-interactive

  echo "→ Switch nginx to SSL config"
  cp nginx.prod.conf nginx/default.conf
  docker compose restart nginx
else
  echo "⚠️  Domain empty — running HTTP only"
fi

echo "✅ Setup complete"


echo "🌐 Server public IP address:"
echo "https://$(curl -s https://checkip.amazonaws.com)/backend"
echo "tracker_admin admin - please change it after first login"
