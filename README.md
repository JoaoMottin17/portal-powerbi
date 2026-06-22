# Portal Power BI - Grupo FRT

Portal para compartilhar relatorios do Power BI com autenticacao de usuarios e
**hierarquia de acesso granular por relatorio**, usando **Supabase** como banco.

## Stack
- Streamlit
- Supabase (PostgreSQL via API)

## Requisitos
- Python 3.10+
- Projeto no Supabase

## Configuracao do banco (Supabase)
1. Abra o projeto no Supabase.
2. Va em `SQL Editor`.
3. Instalacao nova: execute o arquivo `supabase_schema.sql`.
4. Atualizando de uma versao anterior (v2): execute `migration_v3.sql`.

> Com `SUPABASE_DB_URL` configurado, a aplicacao cria/atualiza a ESTRUTURA das
> tabelas automaticamente no primeiro boot. O remapeamento das categorias antigas
> tambem e feito pelo app, mas voce pode rodar `migration_v3.sql` para garantir.

## Variaveis de ambiente
Defina as variaveis abaixo no ambiente local ou em `.streamlit/secrets.toml`:

- `SUPABASE_URL`
- `SUPABASE_KEY` (service role para backend interno)
- `SUPABASE_DB_URL` (para criacao/migracao automatica do schema sem SQL manual)
- `ADMIN_INITIAL_PASSWORD` (obrigatoria apenas se ainda nao existir usuario `admin`)
- `DASH_TOKEN` (opcional; token injetado em paineis Streamlit embedados via iframe)

Exemplo em `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "eyJ..."
SUPABASE_DB_URL = "postgresql://postgres.xxxxx:[SENHA]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
ADMIN_INITIAL_PASSWORD = "troque-esta-senha-forte"
```

## Execucao local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Primeiro acesso
- Usuario: `admin`
- Senha: valor configurado em `ADMIN_INITIAL_PASSWORD`

O usuario admin e criado automaticamente apenas se nao existir e se
`ADMIN_INITIAL_PASSWORD` estiver definido.

## Hierarquia de acesso
O acesso de cada usuario nao-admin a um relatorio e decidido por tres camadas,
combinadas com **E** (todas precisam ser verdadeiras):

1. **Filtro primario — area de atuacao**: a categoria do relatorio precisa estar
   entre as areas permitidas do usuario.
2. **Hierarquia (gestao / operacao)**: `gestao` enxerga relatorios de gestao E de
   operacao; `operacao` enxerga apenas relatorios de operacao.
3. **Filtro secundario — liberacao individual** (restritivo): se o usuario tiver
   relatorios liberados individualmente, ele vera **apenas** esses (sempre dentro
   das areas e do nivel permitidos). Se a lista estiver vazia, ve todos os
   relatorios das suas areas.

O administrador enxerga todos os relatorios e gerencia usuarios. O criador de um
relatorio sempre consegue acessa-lo/edita-lo.

### Areas de atuacao (categorias)
`GERAL`, `FINANCEIRO`, `SUPRIMENTOS`, `INSUMOS`, `MARKETING`, `OPERACIONAL`,
`SOLINFITEC`, `LOGISTICA`, `VENDAS`, `DIRETORIA`, `RH`, `CONTROLADORIA`.

## Arquivos principais
- `app.py`: aplicacao principal (UI + operacoes no Supabase)
- `database.py`: camada central de acesso ao Supabase (auth, hierarquia e CRUD)
- `supabase_schema.sql`: estrutura SQL para instalacao nova
- `migration_v3.sql`: migracao de uma base v2 para a v3 (hierarquia + novas areas)
