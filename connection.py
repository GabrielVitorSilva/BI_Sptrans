# connection.py
import os
import psycopg2
from dotenv import load_dotenv


def get_postgres_connection():
    """
    Cria e retorna uma conexão com o banco PostgreSQL.
    Lê as variáveis de ambiente e configura a conexão apropriada.
    
    Returns:
        psycopg2.connection: Conexão com o banco de dados
        
    Raises:
        RuntimeError: Se as credenciais não estiverem configuradas
    """
    # Tenta ler variáveis de ambiente
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    pg_host = os.getenv("PGHOST")
    pg_port = os.getenv("PGPORT", "5432")
    pg_user = os.getenv("PGUSER")
    pg_password = os.getenv("PGPASSWORD")
    pg_database = os.getenv("PGDATABASE")

    # Se não houver configuração, falha explicitamente
    # Preferir variáveis PG* quando completas; senão usar DATABASE_URL
    use_pg_vars = all([pg_host, pg_user, pg_password, pg_database])
    if not (use_pg_vars or database_url):
        raise RuntimeError("Credenciais do Postgres ausentes: defina PGHOST/PGUSER/PGPASSWORD/PGDATABASE (e opcional PGPORT) ou DATABASE_URL.")

    try:
        if use_pg_vars:
            return psycopg2.connect(host=pg_host, port=pg_port, user=pg_user, password=pg_password, dbname=pg_database)
        else:
            return psycopg2.connect(database_url)
    except Exception as exc:
        raise RuntimeError(f"Falha ao conectar com Postgres: {exc}")
