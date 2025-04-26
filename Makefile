install-db:
	python3 install.py

install:
	cp nginx/nginx.prod.conf nginx/default.conf
	docker-compose up --build -d
	make certificate
	make install-db

install-local:
	cp nginx/nginx.dev.conf nginx/default.conf
	make generate-local-cert
	docker-compose up --build -d
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
	docker-compose down && docker-compose up --build -d

logs:
	docker-compose logs -f

reload-nginx:
	docker exec tracker_nginx nginx -s reload
