#!/bin/bash

set -e

APP_DIR="$HOME/akm-traffic-tracker"
REPO_URL="https://github.com/okhmat-anton/akm-traffic-tracker.git"
DOCKER_COMPOSE_VERSION="2.24.5"

echo "[1/10] Updating system..."
sudo yum update -y

echo "[2/10] Installing Docker..."
sudo amazon-linux-extras enable docker
sudo yum install -y docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "$USER"

echo "[3/10] Installing Docker Compose..."
curl -LO "https://github.com/docker/compose/releases/download/v$DOCKER_COMPOSE_VERSION/docker-compose-linux-x86_64"
sudo mv docker-compose-linux-x86_64 /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

echo "[4/10] Installing Git..."
sudo yum install -y git

echo "[5/10] Cloning project repository..."
mkdir -p "$APP_DIR"
if [ ! -d "$APP_DIR/.git" ]; then
    git clone "$REPO_URL" "$APP_DIR"
else
    echo "Project already cloned at $APP_DIR"
fi

cd "$APP_DIR"

echo "[6/10] Creating .env file if not present..."
cp -n .env.example .env || true

echo "[7/10] Fixing permissions..."
sudo chown -R "$USER":"$USER" "$APP_DIR"

echo "[8/10] Installing make..."
sudo yum install -y make

echo "[9/10] Building and starting Docker services..."
sudo make build
sudo make start

echo "[10/10] Waiting for Nginx container to be ready..."
sleep 15

echo "[11/11] Attempting to run certbot..."
sudo docker exec tracker_nginx certbot --nginx || echo "⚠️  Certbot failed — you may need to adjust Nginx or DNS."

echo
echo "✅ Setup complete. Project is running from: $APP_DIR"
echo "🌐 Server public IP address:"
echo "https://$(curl -s https://checkip.amazonaws.com)/backend"
echo "tracker_admin admin - please change it after first login"
