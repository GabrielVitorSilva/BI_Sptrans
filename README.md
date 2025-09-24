# BI Sptrans - Container Docker

Este projeto é um aplicativo Streamlit que exibe dashboards e relatórios (com geração de PDF) e se conecta ao PostgreSQL para obter contagens de entidades. Abaixo estão as instruções para construir e executar em contêiner Docker.

## Pré-requisitos
- Docker instalado
- (Opcional) Docker Compose
- Credenciais do PostgreSQL disponíveis via variáveis de ambiente

## Variáveis de ambiente
O app lê as credenciais do banco via `connection.py`, aceitando dois formatos:

- Variáveis PG*: `PGHOST`, `PGPORT` (padrão 5432), `PGUSER`, `PGPASSWORD`, `PGDATABASE`
- Ou `DATABASE_URL` no formato `postgres://user:pass@host:port/db` (ou `postgresql://...`)

Você pode usar um arquivo `.env` local (não enviado para o container por padrão) para desenvolvimento, mas no Docker recomenda-se passar via `--env`/`--env-file`.

## Build da imagem

```bash
# No diretório do projeto
docker build -t bi-sptrans:latest .
```

## Executando com Docker (simples)

```bash
# Ajuste as variáveis conforme seu banco
docker run --rm -p 8501:8501 \
  -e PGHOST=seu-host \
  -e PGPORT=5432 \
  -e PGUSER=seu-usuario \
  -e PGPASSWORD=sua-senha \
  -e PGDATABASE=seu-banco \
  --name bi-sptrans \
  bi-sptrans:latest
```

Acesse o app em `http://localhost:8501`.

Se preferir `DATABASE_URL`:

```bash
docker run --rm -p 8501:8501 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  --name bi-sptrans \
  bi-sptrans:latest
```

## Executando com docker compose
Exemplo de arquivo `docker-compose.yml` (apenas serviço do app, conectando a um Postgres externo):

```yaml
services:
  app:
    image: bi-sptrans:latest
    build: .
    ports:
      - "8501:8501"
    environment:
      PGHOST: ${PGHOST}
      PGPORT: ${PGPORT:-5432}
      PGUSER: ${PGUSER}
      PGPASSWORD: ${PGPASSWORD}
      PGDATABASE: ${PGDATABASE}
    # ou use: DATABASE_URL: ${DATABASE_URL}
```

Use um `.env` no mesmo diretório do compose para facilitar:

```env
PGHOST=seu-host
PGPORT=5432
PGUSER=seu-usuario
PGPASSWORD=sua-senha
PGDATABASE=seu-banco
```

Então rode:

```bash
docker compose up --build
```

## Notas
- A imagem expõe a porta 8501 (Streamlit). Se precisar, altere com `-p`.
- O app usa `kaleido` para exportar gráficos no PDF; já está incluído nas dependências.
- Logs aparecem no stdout do container. Para sair: `Ctrl+C` (no compose, `docker compose down`).

## Troubleshooting
- Erro de conexão ao Postgres: verifique variáveis de ambiente e conectividade de rede/firewall.
- Problemas de fonte/locale no PDF: a imagem configura locale `pt_BR.UTF-8`.
- Se a porta 8501 já estiver em uso, mapeie outra: `-p 8080:8501` e acesse `http://localhost:8080`.
