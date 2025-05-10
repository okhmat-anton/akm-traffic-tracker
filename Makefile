install-db:
	docker exec tracker_backend pip install --no-cache-dir -r /app/install/requirements.txt
	docker exec tracker_backend python3 /app/install/install.py

install-prod-domain:
	cp nginx/nginx.prod.conf nginx/default.conf
	docker-compose --compatibility up --build -d
	make certificate
	make install-db

install:
	cp nginx/nginx.dev.conf nginx/default.conf
	make generate-local-cert
	docker-compose --compatibility up --build -d
	make install-db

install-local:
	cp nginx/nginx.dev.conf nginx/default.conf
	make generate-local-cert
	docker-compose --compatibility up --build -d
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
	docker-compose down

restart:
	docker-compose down && docker-compose --compatibility up --build -d

logs:
	docker-compose logs -f

reload-nginx:
	docker exec tracker_nginx nginx -s reload

seed-demo-data:
	docker exec -it tracker_frontend python3 /app/scripts/seed_demo.py