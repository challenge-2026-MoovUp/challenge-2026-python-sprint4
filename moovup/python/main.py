"""Menu de terminal (o mesmo sistema, sem o frontend). Rodar: python python/main.py"""
import json
import oracledb

import db
import servico


def exibir_json():
    try:
        with open(servico.ARQUIVO, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (FileNotFoundError, json.JSONDecodeError):
        print("JSON ainda nao foi gerado.")
        return
    if not dados:
        print("Nenhum usuario no JSON.")
    for usuario in dados:
        print(f"\nNome: {usuario['nome']}")
        print(f"E-mail: {usuario['email']}")
        print(f"Pontos: {usuario['pontos']}")
        print("Historico:")
        for item in usuario["historico"]:
            print("-", item)


def ler_numero(mensagem, minimo, maximo):
    while True:
        try:
            numero = int(input(mensagem))
            if minimo <= numero <= maximo:
                return numero
        except ValueError:
            pass
        print("Opcao invalida.")


def pedir_usuario(conexao, mensagem="E-mail: "):
    usuario = servico.buscar_por_email(conexao, input(mensagem))
    if usuario is None:
        raise ValueError("Usuario nao encontrado.")
    return usuario


# ---------------- acoes (so input/print; as regras estao no servico.py) ----------------
def cadastrar(conexao):
    servico.cadastrar_usuario(conexao, input("Nome: "), input("E-mail: "))
    print("Usuario cadastrado com sucesso!")


def listar(conexao):
    usuarios = servico.listar_usuarios(conexao)
    if not usuarios:
        print("Nenhum usuario cadastrado.")
    for i, u in enumerate(usuarios, start=1):
        print(f"{i} - {u['nome']} | {u['email']} | {u['pontos']} pontos")


def consultar(conexao):
    u = pedir_usuario(conexao)
    print(f"Nome: {u['nome']}\nE-mail: {u['email']}\nPontos: {u['pontos']}")


def editar(conexao):
    u = pedir_usuario(conexao, "E-mail atual: ")
    nome = input(f"Novo nome [{u['nome']}]: ")
    email = input(f"Novo e-mail [{u['email']}]: ")
    servico.editar_usuario(conexao, u["id"], nome, email)
    print("Usuario atualizado!")


def excluir(conexao):
    u = pedir_usuario(conexao)
    if input(f"Excluir {u['nome']}? (S/N): ").strip().upper() == "S":
        servico.excluir_usuario(conexao, u["id"])
        print("Usuario excluido!")
    else:
        print("Exclusao cancelada.")


def postagem(conexao):
    u = pedir_usuario(conexao, "Seu e-mail: ")
    tipos = list(servico.POSTAGENS)
    for i, tipo in enumerate(tipos, start=1):
        print(f"{i} - {tipo} (+{servico.POSTAGENS[tipo]} pontos)")
    tipo = tipos[ler_numero("Escolha o tipo: ", 1, len(tipos)) - 1]
    quantidade = ler_numero("Quantidade (1 a 5): ", 1, 5)
    novo = servico.registrar_postagem(conexao, u["id"], tipo, quantidade)
    print(f"Voce ganhou {novo['pontos'] - u['pontos']} pontos!")


def converter(conexao):
    u = pedir_usuario(conexao, "Seu e-mail: ")
    print(f"Cada ponto vale R$ {servico.VALOR_POR_PONTO:.4f}.")
    resultado = servico.converter_pontos(conexao, u["id"], input("Quantos pontos deseja converter? "))
    print(f"Valor estimado: R$ {resultado['valor']:.2f}")


def saldo(conexao):
    u = pedir_usuario(conexao, "Seu e-mail: ")
    print(f"\nNome: {u['nome']}\nPontos: {u['pontos']}")
    print(f"Valor estimado: R$ {u['pontos'] * servico.VALOR_POR_PONTO:.2f}\nHistorico:")
    for item in servico.listar_historico(conexao, u["id"]):
        print("-", item)


def executar(acao, conexao):
    """Roda uma acao; se der erro, mostra a mensagem e desfaz o que for do banco."""
    try:
        acao(conexao)
    except ValueError as erro:
        print(erro)
    except oracledb.Error as erro:
        conexao.rollback()
        print(f"Erro no banco de dados: {erro}")
    except OSError:
        print("Nao foi possivel gravar o arquivo JSON.")


def menu_usuarios(conexao):
    acoes = {"1": cadastrar, "2": listar, "3": consultar, "4": editar, "5": excluir}
    while True:
        print("\n1 - Cadastrar | 2 - Listar | 3 - Consultar")
        print("4 - Editar | 5 - Excluir | 0 - Voltar")
        opcao = input("Opcao: ")
        if opcao == "0":
            break
        if opcao in acoes:
            executar(acoes[opcao], conexao)
        else:
            print("Opcao invalida.")


def menu(conexao):
    acoes = {"2": postagem, "3": converter, "4": saldo}
    while True:
        print("\n===== SOUL UP =====")
        print("1 - Usuarios\n2 - Registrar postagem\n3 - Converter pontos")
        print("4 - Consultar saldo\n5 - Exibir JSON\n0 - Sair")
        opcao = input("Opcao: ")
        if opcao == "1":
            menu_usuarios(conexao)
        elif opcao in acoes:
            executar(acoes[opcao], conexao)
        elif opcao == "5":
            exibir_json()
        elif opcao == "6":
            servico.exportar_json()
        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    try:
        conexao = db.conectar()
    except oracledb.Error as erro:
        print(f"Nao foi possivel conectar ao Oracle: {erro}")
    else:
        try:
            servico.exportar_json(conexao)  # JSON sincronizado com o banco ao iniciar
            menu(conexao)
        finally:
            conexao.close()
