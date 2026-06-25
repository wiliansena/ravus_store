# Ravus Store

MVP simples para controle de loja de roupa com Python, Postgres e Jinja.

## Recursos

- Cadastros de categoria, marca, cor, tamanho, fornecedor, cliente e produto.
- Produto com variações por cor/tamanho, foto, preço e estoque mínimo.
- Entradas e ajustes de estoque.
- Venda balcão com desconto, forma de pagamento e recibo.
- Catálogo público com botão de WhatsApp.
- Relatórios de vendas por período, produtos mais vendidos e estoque baixo.
- Usuários, perfis e permissões simples.
- Login/logout com usuário administrador inicial.

## Como rodar

1. Crie o banco no Postgres:

```sql
CREATE DATABASE ravus_store;
```

2. Crie o ambiente e instale dependências:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. Copie `.env.example` para `.env` e ajuste `DATABASE_URL` e `WHATSAPP_NUMBER`.

4. Inicialize o banco e rode:

```powershell
flask db init
flask db migrate -m "initial"
flask db upgrade
flask seed
flask run
```

O `flask seed` cria o primeiro administrador com os dados do `.env`:

```text
ADMIN_EMAIL=admin@ravus.local
ADMIN_PASSWORD=admin123
```

Para recriar ou resetar o admin padrão:

```powershell
python criar_admin.py
```

O administrador também pode redefinir a senha de qualquer usuário pela tela
`Usuários`, informando a nova senha na tabela de usuários cadastrados.

Para começar sem migrações, também funciona:

```powershell
.venv\Scripts\python app.py --init-db
.venv\Scripts\python app.py
```

Depois acesse `http://127.0.0.1:5000`.
