"""Regras do sistema + SQL. Sem input() e sem print(): serve ao menu (main.py) e ao Flask (app.py).
Erros de validação viram ValueError com a mensagem que o usuário vai ler."""
import json

ARQUIVO = "usuarios.json"
VALOR_POR_PONTO = 0.0091
POSTAGENS = {"foto": 5, "video": 15, "story": 3, "reels": 20}


def config():
    return {
        "valor_ponto": VALOR_POR_PONTO,
        "postagens": [{"id": tipo, "pontos": pts} for tipo, pts in POSTAGENS.items()],
    }


def _inteiro(valor, mensagem):
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError(mensagem)


# ---------------- JSON (espelho do banco) ----------------
def exportar_json(conexao):
    lista = []
    with conexao.cursor() as cursor:
        cursor.execute("SELECT id_usuario, nome, email, pontos FROM usuario ORDER BY id_usuario")
        for id_usuario, nome, email, pontos in cursor.fetchall():
            historico = listar_historico(conexao, id_usuario)
            lista.append({"nome": nome, "email": email, "pontos": int(pontos), "historico": historico})
    with open(ARQUIVO, "w", encoding="utf-8") as arquivo:
        json.dump(lista, arquivo, indent=4, ensure_ascii=False)


# ---------------- Busca ----------------
def _usuario(linha):
    return {"id": linha[0], "nome": linha[1], "email": linha[2], "pontos": int(linha[3])}


def buscar_por_email(conexao, email):
    """Retorna o usuário (dict) ou None."""
    with conexao.cursor() as cursor:
        cursor.execute(
            "SELECT id_usuario, nome, email, pontos FROM usuario WHERE email = :1",
            ((email or "").strip().lower(),),
        )
        linha = cursor.fetchone()
    return _usuario(linha) if linha else None


def obter_usuario(conexao, id_usuario):
    """Retorna o usuário (dict) ou levanta ValueError."""
    with conexao.cursor() as cursor:
        cursor.execute(
            "SELECT id_usuario, nome, email, pontos FROM usuario WHERE id_usuario = :1",
            (id_usuario,),
        )
        linha = cursor.fetchone()
    if linha is None:
        raise ValueError("Usuário não encontrado.")
    return _usuario(linha)


def entrar(conexao, email):
    usuario = buscar_por_email(conexao, email)
    if usuario is None:
        raise ValueError("Nenhum usuário com esse e-mail. Crie uma conta.")
    return usuario


# ---------------- CRUD ----------------
def cadastrar_usuario(conexao, nome, email):
    nome = (nome or "").strip()
    email = (email or "").strip().lower()
    if not nome or "@" not in email:
        raise ValueError("Nome ou e-mail inválido.")
    if buscar_por_email(conexao, email):
        raise ValueError("Este e-mail já está cadastrado.")
    with conexao.cursor() as cursor:
        cursor.execute("INSERT INTO usuario (nome, email, pontos) VALUES (:1, :2, 0)", (nome, email))
    conexao.commit()
    exportar_json(conexao)
    return buscar_por_email(conexao, email)


def listar_usuarios(conexao):
    with conexao.cursor() as cursor:
        cursor.execute("SELECT id_usuario, nome, email, pontos FROM usuario ORDER BY id_usuario")
        return [_usuario(linha) for linha in cursor.fetchall()]


def editar_usuario(conexao, id_usuario, nome, email):
    usuario = obter_usuario(conexao, id_usuario)
    nome = (nome or "").strip() or usuario["nome"]
    email = (email or "").strip().lower() or usuario["email"]
    if "@" not in email:
        raise ValueError("E-mail inválido.")
    outro = buscar_por_email(conexao, email)
    if outro and outro["id"] != usuario["id"]:
        raise ValueError("Este e-mail já está cadastrado.")
    with conexao.cursor() as cursor:
        cursor.execute(
            "UPDATE usuario SET nome = :1, email = :2 WHERE id_usuario = :3",
            (nome, email, id_usuario),
        )
    conexao.commit()
    exportar_json(conexao)
    return obter_usuario(conexao, id_usuario)


def excluir_usuario(conexao, id_usuario):
    obter_usuario(conexao, id_usuario)
    with conexao.cursor() as cursor:  # o histórico some junto (ON DELETE CASCADE)
        cursor.execute("DELETE FROM usuario WHERE id_usuario = :1", (id_usuario,))
    conexao.commit()
    exportar_json(conexao)


# ---------------- Postagens, conversão e histórico ----------------
def registrar_postagem(conexao, id_usuario, tipo, quantidade):
    obter_usuario(conexao, id_usuario)
    if tipo not in POSTAGENS:
        raise ValueError("Tipo de postagem inválido.")
    quantidade = _inteiro(quantidade, "Quantidade inválida.")
    if not 1 <= quantidade <= 5:
        raise ValueError("Informe de 1 a 5 postagens.")
    ganhos = POSTAGENS[tipo] * quantidade
    with conexao.cursor() as cursor:
        cursor.execute(
            "UPDATE usuario SET pontos = pontos + :1 WHERE id_usuario = :2", (ganhos, id_usuario)
        )
        cursor.execute(
            "INSERT INTO historico (id_usuario, descricao) VALUES (:1, :2)",
            (id_usuario, f"{quantidade}x {tipo}: +{ganhos} pontos"),
        )
    conexao.commit()  # um único commit: grava os dois ou nenhum
    exportar_json(conexao)
    return obter_usuario(conexao, id_usuario)


def converter_pontos(conexao, id_usuario, pontos):
    usuario = obter_usuario(conexao, id_usuario)
    usar = _inteiro(pontos, "Digite apenas números para a quantidade de pontos.")
    if usuario["pontos"] == 0:
        raise ValueError("Você não possui pontos para converter.")
    if usar < 1 or usar > usuario["pontos"]:
        raise ValueError("Quantidade de pontos inválida.")
    valor = usar * VALOR_POR_PONTO
    with conexao.cursor() as cursor:
        cursor.execute(
            "UPDATE usuario SET pontos = pontos - :1 WHERE id_usuario = :2 AND pontos >= :3",
            (usar, id_usuario, usar),
        )
        if cursor.rowcount == 0:
            raise ValueError("Saldo insuficiente.")
        cursor.execute(
            "INSERT INTO historico (id_usuario, descricao) VALUES (:1, :2)",
            (id_usuario, f"Conversao: -{usar} pontos = R$ {valor:.2f}"),
        )
    conexao.commit()
    exportar_json(conexao)
    return {"usuario": obter_usuario(conexao, id_usuario), "valor": round(valor, 2)}


def listar_historico(conexao, id_usuario):
    with conexao.cursor() as cursor:
        cursor.execute(
            "SELECT descricao FROM historico WHERE id_usuario = :1 ORDER BY id_historico",
            (id_usuario,),
        )
        return [linha[0] for linha in cursor.fetchall()]
