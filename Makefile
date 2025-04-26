install:
	ln -sf ./nginx/nginx.prod.conf ./nginx/default.conf
	docker-compose up --build -d
	make certificate

install-local:
	ln -sf ./nginx/nginx.dev.conf ./nginx/default.conf
	make generate-local-cert
	docker-compose up --build -d

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
	docker-compose down && docker-compose up --build -d

logs:
	docker-compose logs -f
