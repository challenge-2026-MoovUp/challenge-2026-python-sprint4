"""Controller: recebe as requisições do frontend e chama o servico.py.
Rodar:  python app.py   ->   http://localhost:5000"""
import oracledb
from flask import Flask, g, jsonify, request, send_from_directory

import db
import servico

app = Flask(__name__, static_folder="static")


def conexao():
    """Uma conexão do pool por requisição (fechada em fechar_conexao)."""
    if "conexao" not in g:
        g.conexao = db.obter_conexao()
    return g.conexao


@app.teardown_appcontext
def fechar_conexao(_erro):
    c = g.pop("conexao", None)
    if c is not None:
        c.close()


@app.errorhandler(ValueError)  # validações do servico.py -> erro 400 com a mensagem
def erro_validacao(e):
    return jsonify(erro=str(e)), 400


@app.errorhandler(oracledb.Error)
def erro_banco(e):
    if "conexao" in g:
        g.conexao.rollback()
    app.logger.error("Erro Oracle: %s", e)
    return jsonify(erro="Erro no banco de dados. Tente novamente."), 500


def corpo():
    return request.get_json(silent=True) or {}


@app.get("/")
def home():
    return send_from_directory("static", "index.html")


@app.get("/api/config")
def config():
    return jsonify(servico.config())


@app.post("/api/login")
def login():
    return jsonify(servico.entrar(conexao(), corpo().get("email")))


@app.post("/api/usuarios")
def criar():
    d = corpo()
    return jsonify(servico.cadastrar_usuario(conexao(), d.get("nome"), d.get("email"))), 201


@app.get("/api/usuarios/<int:uid>")
def ler(uid):
    return jsonify(servico.obter_usuario(conexao(), uid))


@app.put("/api/usuarios/<int:uid>")
def atualizar(uid):
    d = corpo()
    return jsonify(servico.editar_usuario(conexao(), uid, d.get("nome"), d.get("email")))


@app.delete("/api/usuarios/<int:uid>")
def excluir(uid):
    servico.excluir_usuario(conexao(), uid)
    return jsonify(ok=True)


@app.post("/api/usuarios/<int:uid>/postagem")
def postagem(uid):
    d = corpo()
    return jsonify(servico.registrar_postagem(conexao(), uid, d.get("tipo"), d.get("quantidade")))


@app.post("/api/usuarios/<int:uid>/converter")
def converter(uid):
    return jsonify(servico.converter_pontos(conexao(), uid, corpo().get("pontos")))


@app.get("/api/usuarios/<int:uid>/historico")
def historico(uid):
    servico.obter_usuario(conexao(), uid)
    return jsonify(servico.listar_historico(conexao(), uid))


if __name__ == "__main__":
    app.run(debug=True)
