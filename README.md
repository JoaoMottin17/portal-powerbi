# Portal Power BI - Grupo FRT

Portal para compartilhar relatorios do Power BI com autenticacao de usuarios, agora usando **Supabase** como banco de dados.

## Stack
- Streamlit
- Supabase (PostgreSQL via API)

## Requisitos
- Python 3.10+
- Projeto no Supabase

## Configuracao do banco (Supabase)
1. Abra o projeto no Supabase.
2. Va em `SQL Editor`.
3. Execute o arquivo `supabase_schema.sql`.

## Variaveis de ambiente
Defina as variaveis abaixo no ambiente local ou em `.streamlit/secrets.toml`:

- `SUPABASE_URL`
- `SUPABASE_KEY` (service role para backend interno)
- `SUPABASE_DB_URL` (para criacao automatica do schema sem SQL manual)
- `ADMIN_INITIAL_PASSWORD` (obrigatoria apenas se ainda nao existir usuario `admin`)

Exemplo em `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "eyJ..."
SUPABASE_DB_URL = "postgresql://postgres.xxxxx:[SENHA]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
ADMIN_INITIAL_PASSWORD = "troque-esta-senha-forte"
```

Com `SUPABASE_DB_URL` configurado, a aplicacao cria tabelas/indices/trigger automaticamente no primeiro boot.

## Execucao local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Primeiro acesso
- Usuario: `admin`
- Senha: valor configurado em `ADMIN_INITIAL_PASSWORD`

O usuario admin e criado automaticamente apenas se nao existir e se `ADMIN_INITIAL_PASSWORD` estiver definido.

## Arquivos principais
- `app.py`: aplicacao principal (UI + operacoes no Supabase)
- `database.py`: camada central de acesso ao Supabase (autenticacao e CRUD)
- `supabase_schema.sql`: estrutura SQL para criar tabelas no Supabase
