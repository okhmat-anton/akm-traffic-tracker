from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

import subprocess
from pathlib import Path

import asyncio

router = APIRouter()


@router.get("/domain_ping", response_class=PlainTextResponse)
def ping():
    return "OK"


@router.get("/domain_update_nginx_and_ssl")
async def create_nginx(request: Request, domain_id: int):
    pg = request.app.state.pg

    async with pg.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT domain
            FROM domains
            WHERE id = $1
        """, domain_id)

    if not row:
        raise HTTPException(status_code=404, detail="Domain not found")

    async with pg.acquire() as conn:
        await conn.fetchrow("""
            UPDATE domains
            SET updated_at = NOW(), ssl_status= 'pending'
            WHERE id = $1
        """, domain_id)

    domain = row["domain"]
    path = await generate_nginx_conf(domain, domain_id)

    if path:
        async with pg.acquire() as conn:
            await conn.fetchrow("""
                UPDATE domains
                SET updated_at = NOW(), ssl_status= 'success'
                WHERE id = $1
            """, domain_id)

    return {"status": "ok", "file": str(path)}

async def request_ssl_letsencrypt(domain: str) -> bool:
    try:
        email = f"admin@{domain}"

        result = subprocess.run([
            "certbot", "certonly", "--webroot",
            "-w", "/var/www/certbot",  # корень для ACME challenge
            "-d", domain,
            "--agree-tos",
            "--email", email,
            "--non-interactive"
        ], check=True)

        cert_path = Path(f"/etc/letsencrypt/live/{domain}/fullchain.pem")

        for _ in range(300):  # 10 minutes
            if cert_path.exists():
                print(f"✅ Сертификат найден: {cert_path}")
                return True
            await asyncio.sleep(2)

        return cert_path.exists()

    except subprocess.CalledProcessError as e:
        print(f"❌ Certbot failed for {domain}: {e}")
        return False


def reload_nginx():
    # subprocess.run(["docker", "stop", "tracker_nginx"], check=True)
    # subprocess.run(["docker", "start", "tracker_nginx"], check=True)
    subprocess.run([
        "docker", "exec", "tracker_nginx", "nginx", "-s", "reload"
    ])


async def generate_nginx_conf(domain: str, domain_id: int) -> Path:
    template_path = Path("/var/www/nginx/_domain_nginx.prod.conf")
    output_dir = Path("/var/www/nginx/domains")

    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    if await request_ssl_letsencrypt(domain):
        # Читаем шаблон
        content = template_path.read_text()

        # Заменяем плейсхолдер
        updated = content.replace("server_name _;", f"server_name {domain};")
        updated = updated.replace("yourdomain.com", domain)

        # Создаём целевой путь
        output_dir.mkdir(parents=True, exist_ok=True)
        target_path = output_dir / f"{domain_id}_{domain}.conf"

        if not target_path.exists() or target_path.read_text() != updated:
            target_path.write_text(updated)
            reload_nginx()
            print(f"✅ Updated: {target_path}")
        else:
            print(f"ℹ️ No changes: {target_path}")
    else:
        raise HTTPException(status_code=500, detail="SSL certificate request failed")

    return target_path
