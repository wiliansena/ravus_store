# Deploy Ravus Store

Este guia separa duas coisas:

- Codigo do sistema: vai pelo Git.
- Dados da loja: banco PostgreSQL e arquivos de `static/uploads`, enviados por backup.

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

Arquivos que nao devem ir para o Git:

- `.env`
- `.venv/`
- `static/uploads/`
- backups `.dump`, `.backup`, `.sql`, `.zip`

## 2. Preparar projeto na VPS

Exemplo usando `/var/www/ravus-store`:

```bash
cd /var/www
git clone URL_DO_REPOSITORIO ravus-store
cd ravus-store
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crie o arquivo `.env` na VPS:

```bash
nano .env
```

Exemplo:

```env
FLASK_APP=run.py
FLASK_ENV=production
FLASK_RUN_HOST=127.0.0.1
FLASK_RUN_PORT=5022
DATABASE_URL=postgresql+psycopg://USUARIO:SENHA@localhost:5432/ravus_store
SECRET_KEY=COLOQUE_UMA_CHAVE_FORTE_AQUI
WHATSAPP_NUMBER=5581999999999
ADMIN_NAME=Administrador
ADMIN_EMAIL=admin@ravus.local
ADMIN_PASSWORD=admin123
TIMEZONE=America/Sao_Paulo
```

## 3. Fazer backup do banco local

No computador local:

```powershell
pg_dump -h localhost -U postgres -Fc -d ravus_store -f ravus_store.dump
```

Se o nome do banco local for outro, troque `ravus_store` pelo nome correto.

## 4. Fazer backup das imagens locais

No computador local:

```powershell
Compress-Archive -Path static\uploads -DestinationPath ravus_uploads.zip -Force
```

## 5. Enviar backup para a VPS

No computador local:

```powershell
scp ravus_store.dump usuario@IP_DA_VPS:/var/www/ravus-store/
scp ravus_uploads.zip usuario@IP_DA_VPS:/var/www/ravus-store/
```

## 6. Restaurar banco na VPS

Na VPS:

```bash
cd /var/www/ravus-store
createdb ravus_store
pg_restore -h localhost -U postgres -d ravus_store --clean --if-exists ravus_store.dump
source .venv/bin/activate
flask db upgrade
```

## 7. Restaurar imagens na VPS

Na VPS:

```bash
cd /var/www/ravus-store
unzip -o ravus_uploads.zip
```

Confirme que existe:

```bash
ls static/uploads
```

## 8. Rodar com Gunicorn

Teste manual:

```bash
cd /var/www/ravus-store
source .venv/bin/activate
gunicorn -w 3 -b 127.0.0.1:8002 wsgi:app
```

## 9. Systemd

Crie o servico:

```bash
sudo nano /etc/systemd/system/ravus-store.service
```

Conteudo:

```ini
[Unit]
Description=Ravus Store
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/ravus-store
EnvironmentFile=/var/www/ravus-store/.env
ExecStart=/var/www/ravus-store/.venv/bin/gunicorn -w 3 -b 127.0.0.1:8002 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Ative:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ravus-store
sudo systemctl start ravus-store
sudo systemctl status ravus-store
```

## 10. Nginx e dominio

Crie o arquivo:

```bash
sudo nano /etc/nginx/sites-available/ravus-store
```

Conteudo:

```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;

    location /static/ {
        alias /var/www/ravus-store/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ative:

```bash
sudo ln -s /etc/nginx/sites-available/ravus-store /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Depois aponte o DNS do dominio para o IP da VPS e ative SSL:

```bash
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```
