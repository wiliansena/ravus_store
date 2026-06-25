# Deploy Ravus Store

Este projeto vai seguir o mesmo padrao usado no SaaSForce:

- Ubuntu na VPS
- Flask
- venv
- PostgreSQL
- Waitress
- systemd

Para usar dominio sem porta e com HTTPS, o Waitress continua rodando a aplicacao e o Nginx fica somente como proxy do dominio.

## 1. Enviar codigo para o Git

No computador local:

```powershell
git status
git remote add origin URL_DO_REPOSITORIO
git branch -M main
git push -u origin main
```

Se o remoto ja existir:

```powershell
git remote set-url origin URL_DO_REPOSITORIO
git push -u origin main
```

O Git envia o codigo. Ele nao envia:

- `.env`
- `.venv/`
- `static/uploads/`
- backups `.dump`, `.backup`, `.sql`, `.zip`

## 2. Instalar dependencias na VPS

Na VPS, fora do venv:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git postgresql postgresql-contrib build-essential libpq-dev locales unzip
sudo locale-gen pt_BR.UTF-8
sudo update-locale LANG=pt_BR.UTF-8
```

Depois saia e entre novamente no SSH.

## 3. Clonar o projeto na VPS

Na VPS:

```bash
cd /var/www
sudo mkdir ravus_store
sudo chown $USER:$USER ravus_store
cd ravus_store
git clone URL_DO_REPOSITORIO .
```

## 4. Criar venv e instalar dependencias

Na VPS:

```bash
cd /var/www/ravus_store
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Criar o .env na VPS

Na VPS:

```bash
nano .env
```

Exemplo:

```env
FLASK_APP=run.py
FLASK_ENV=production
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5022
DATABASE_URL=postgresql+psycopg://ravus_store:SENHA_FORTE@localhost:5432/ravus_store
SECRET_KEY=COLOQUE_UMA_CHAVE_FORTE_AQUI
WHATSAPP_NUMBER=5581999999999
ADMIN_NAME=Administrador
ADMIN_EMAIL=admin@ravus.local
ADMIN_PASSWORD=admin123
TIMEZONE=America/Sao_Paulo
```

## 6. Criar banco na VPS

Na VPS, fora do venv:

```bash
sudo -u postgres psql
```

Dentro do PostgreSQL:

```sql
CREATE DATABASE ravus_store;
CREATE USER ravus_store WITH PASSWORD 'SENHA_FORTE';
GRANT ALL PRIVILEGES ON DATABASE ravus_store TO ravus_store;
\q
```

## 7. Fazer backup do banco local

No computador local:

```powershell
pg_dump -h localhost -U postgres -Fc -d ravus_store -f ravus_store.dump
```

Se o banco local tiver outro nome, troque `ravus_store` pelo nome correto.

## 8. Fazer backup das imagens locais

No computador local:

```powershell
Compress-Archive -Path static\uploads -DestinationPath ravus_uploads.zip -Force
```

## 9. Enviar backups para a VPS

No computador local:

```powershell
scp ravus_store.dump usuario@IP_DA_VPS:/var/www/ravus_store/
scp ravus_uploads.zip usuario@IP_DA_VPS:/var/www/ravus_store/
```

## 10. Restaurar banco na VPS

Na VPS:

```bash
cd /var/www/ravus_store
pg_restore -h localhost -U postgres -d ravus_store --clean --if-exists ravus_store.dump
source venv/bin/activate
flask db upgrade
```

## 11. Restaurar imagens na VPS

Na VPS:

```bash
cd /var/www/ravus_store
unzip -o ravus_uploads.zip
ls static/uploads
```

## 12. Testar com Waitress

Na VPS, dentro do venv:

```bash
cd /var/www/ravus_store
source venv/bin/activate
waitress-serve --host=0.0.0.0 --port=8001 wsgi:app
```

Acesse:

```text
http://IP_DA_VPS:8001
```

## 13. Criar servico systemd

Na VPS:

```bash
sudo nano /etc/systemd/system/ravus_store.service
```

Conteudo:

```ini
[Unit]
Description=Ravus Store Flask App (Waitress)
After=network.target

[Service]
User=wilian
WorkingDirectory=/var/www/ravus_store
EnvironmentFile=/var/www/ravus_store/.env
ExecStart=/var/www/ravus_store/venv/bin/waitress-serve --host=0.0.0.0 --port=8001 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Ativar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ravus_store
sudo systemctl start ravus_store
sudo systemctl status ravus_store
```

## 14. Dominio com Nginx

Se quiser acessar sem porta, exemplo `https://achadinhoskids.store`, use Nginx como proxy.

Na VPS:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo nano /etc/nginx/sites-available/ravus_store
```

Conteudo:

```nginx
server {
    listen 80;
    server_name achadinhoskids.store www.achadinhoskids.store;

    location /static/ {
        alias /var/www/ravus_store/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ativar:

```bash
sudo ln -s /etc/nginx/sites-available/ravus_store /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Depois aponte o DNS do dominio para o IP da VPS e ative SSL:

```bash
sudo certbot --nginx -d achadinhoskids.store -d www.achadinhoskids.store
```

## 15. Atualizar sistema futuramente

Na VPS:

```bash
cd /var/www/ravus_store
git pull
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart ravus_store
```
