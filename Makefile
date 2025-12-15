
COMPOSE = COMPOSE

install-db:
	docker exec tracker_backend pip install --no-cache-dir -r /app/install/requirements.txt
	docker exec tracker_backend python3 /app/install/install.py

install-prod-domain:
	cp nginx/nginx.prod.conf nginx/default.conf
	COMPOSE --compatibility up --build -d
	make certificate
	make install-db

install:
	cp nginx/nginx.dev.conf nginx/default.conf
	make generate-local-cert
	COMPOSE --compatibility up --build -d
	make install-db

install-local:
	cp nginx/nginx.dev.conf nginx/default.conf
	make generate-local-cert
	COMPOSE --compatibility up --build -d
	make install-db

generate-local-cert:
	mkdir -p ssl
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout ssl/selfsigned.key \
		-out ssl/selfsigned.crt \
		-subj "/C=US/ST=Local/L=Local/O=Dev/OU=Dev/CN=localhost"

certificate:
	docker exec tracker_nginx certbot --nginx

stop:
	COMPOSE down

start:
	COMPOSE --compatibility up --build -d

restart:
	COMPOSE down && COMPOSE --compatibility up --build -d

logs:
	COMPOSE logs -f

reload-nginx:
	docker exec tracker_nginx nginx -s reload

seed-demo-data:
	docker exec -it tracker_frontend python3 /app/scripts/seed_demo.py

build:
	COMPOSE build

start:
	COMPOSE up -d

start-http:
	COMPOSE up -d nginx backend frontend

restart-nginx:
	COMPOSE restart nginx

clear-logs:

	@echo "Stopping containers..."
	$(COMPOSE) down
	@echo "Truncating logs..."
	sudo truncate -s 0 /var/lib/docker/containers/*/*-json.log || true
	@echo "Logs cleared."

	@echo "Clearing logs..."
	$(COMPOSE) logs --no-color > /dev/null 2>&1 || true
	@docker system prune -f --volumes
	@echo "Logs cleared (via prune)."
	rm -f logs/*.log || true
	@echo "Log files removed"

	make start