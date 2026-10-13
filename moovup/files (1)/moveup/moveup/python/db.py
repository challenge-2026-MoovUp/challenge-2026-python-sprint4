"""Conexão com o Oracle. Usuário e senha ficam no arquivo .env (nunca no código)."""
import os
import oracledb
from dotenv import load_dotenv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent  # pasta moveup/

load_dotenv(RAIZ / ".env")          # se existir, tem prioridade
load_dotenv(RAIZ / ".env.example")


def _parametros():
    return {
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "dsn": os.environ.get("DB_DSN", "oracle.fiap.com.br:1521/ORCL"),
    }


def conectar():
    """Uma conexão simples (usada pelo menu de terminal, main.py)."""
    return oracledb.connect(**_parametros())


_pool = None


def obter_conexao():
    """Pega uma conexão do pool (usada pelo Flask). conexao.close() devolve ao pool."""
    global _pool
    if _pool is None:
        _pool = oracledb.create_pool(min=1, max=4, increment=1, **_parametros())
    return _pool.acquire()
