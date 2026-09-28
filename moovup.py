import json
import oracledb

ARQUIVO = "usuarios.json"
VALOR_POR_PONTO = 0.0091
postagens = {
    "foto": 5,
    "video": 15,
    "story": 3,
    "reels": 20
}


# ---------------------------------------------------------
# CONEXAO
# ---------------------------------------------------------
def conectar():
    """Abre a conexao com o Oracle (uma vez so, para o sistema todo)."""
    return oracledb.connect(
        user="rm573469",
        password="270807",
        dsn="oracle.fiap.com.br:1521/ORCL"
    )


# ---------------------------------------------------------
# JSON (somente exibicao dos campos que estao no banco)
# ---------------------------------------------------------
def exportar_json(conexao):
    """Le os dados do Oracle e grava no JSON, no mesmo formato de antes."""
    lista = []
    with conexao.cursor() as cursor:
        cursor.execute("SELECT id_usuario, nome, email, pontos FROM usuario ORDER BY id_usuario")
        linhas = cursor.fetchall()

        for id_usuario, nome, email, pontos in linhas:
            cursor.execute(
                "SELECT descricao FROM historico WHERE id_usuario = :1 ORDER BY id_historico",
                (id_usuario,)
            )
            historico = [linha[0] for linha in cursor.fetchall()]
            lista.append({
                "nome": nome,
                "email": email,
                "pontos": int(pontos),
                "historico": historico
            })

    with open(ARQUIVO, "w", encoding="utf-8") as arquivo:
        json.dump(lista, arquivo, indent=4, ensure_ascii=False)


def exibir_json():
    """Mostra o conteudo do JSON (que espelha o banco)."""
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as arquivo:
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


# ---------------------------------------------------------
# FUNCOES AUXILIARES
# ---------------------------------------------------------
def buscar_usuario(conexao, email):
    """Retorna um dicionario com o usuario do banco, ou None."""
    with conexao.cursor() as cursor:
        cursor.execute(
            "SELECT id_usuario, nome, email, pontos FROM usuario WHERE email = :1",
            (email.strip().lower(),)
        )
        linha = cursor.fetchone()

    if linha is None:
        return None
    return {"id": linha[0], "nome": linha[1], "email": linha[2], "pontos": int(linha[3])}


def ler_numero(mensagem, minimo, maximo):
    """Le um numero inteiro dentro de um intervalo."""
    while True:
        try:
            numero = int(input(mensagem))
            if minimo <= numero <= maximo:
                return numero
        except ValueError:
            pass
        print("Opcao invalida.")


# ---------------------------------------------------------
# CRUD DE USUARIOS (Oracle)
# ---------------------------------------------------------
def cadastrar_usuario(conexao):
    nome = input("Nome: ").strip()
    email = input("E-mail: ").strip().lower()

    if not nome or "@" not in email:
        print("Nome ou e-mail invalido.")
    elif buscar_usuario(conexao, email):
        print("Este e-mail ja esta cadastrado.")
    else:
        with conexao.cursor() as cursor:
            cursor.execute(
                "INSERT INTO usuario (nome, email, pontos) VALUES (:1, :2, 0)",
                (nome, email)
            )
        conexao.commit()
        exportar_json(conexao)
        print("Usuario cadastrado com sucesso!")


def listar_usuarios(conexao):
    with conexao.cursor() as cursor:
        cursor.execute("SELECT nome, email, pontos FROM usuario ORDER BY id_usuario")
        linhas = cursor.fetchall()

    if not linhas:
        print("Nenhum usuario cadastrado.")
    for indice, (nome, email, pontos) in enumerate(linhas, start=1):
        print(f"{indice} - {nome} | {email} | {pontos} pontos")


def consultar_usuario(conexao):
    usuario = buscar_usuario(conexao, input("E-mail: "))
    if usuario:
        print(f"Nome: {usuario['nome']}")
        print(f"E-mail: {usuario['email']}")
        print(f"Pontos: {usuario['pontos']}")
    else:
        print("Usuario nao encontrado.")


def editar_usuario(conexao):
    usuario = buscar_usuario(conexao, input("E-mail atual: "))
    if not usuario:
        print("Usuario nao encontrado.")
        return

    nome = input(f"Novo nome [{usuario['nome']}]: ").strip() or usuario["nome"]
    email = input(f"Novo e-mail [{usuario['email']}]: ").strip().lower() or usuario["email"]

    if "@" not in email:
        print("E-mail invalido.")
        return

    outro_usuario = buscar_usuario(conexao, email)
    if outro_usuario and outro_usuario["id"] != usuario["id"]:
        print("Este e-mail ja esta cadastrado.")
        return

    with conexao.cursor() as cursor:
        cursor.execute(
            "UPDATE usuario SET nome = :1, email = :2 WHERE id_usuario = :3",
            (nome, email, usuario["id"])
        )
    conexao.commit()
    exportar_json(conexao)
    print("Usuario atualizado!")


def excluir_usuario(conexao):
    usuario = buscar_usuario(conexao, input("E-mail: "))
    if not usuario:
        print("Usuario nao encontrado.")
        return

    confirmar = input(f"Excluir {usuario['nome']}? (S/N): ").strip().upper()
    if confirmar == "S":
        # O historico e apagado junto (ON DELETE CASCADE)
        with conexao.cursor() as cursor:
            cursor.execute("DELETE FROM usuario WHERE id_usuario = :1", (usuario["id"],))
        conexao.commit()
        exportar_json(conexao)
        print("Usuario excluido!")
    else:
        print("Exclusao cancelada.")


# ---------------------------------------------------------
# POSTAGENS, CONVERSAO E SALDO
# ---------------------------------------------------------
def registrar_postagem(conexao):
    usuario = buscar_usuario(conexao, input("Seu e-mail: "))
    if not usuario:
        print("Usuario nao encontrado.")
        return

    tipos = list(postagens)
    for indice, tipo in enumerate(tipos, start=1):
        print(f"{indice} - {tipo} (+{postagens[tipo]} pontos)")

    tipo = tipos[ler_numero("Escolha o tipo: ", 1, len(tipos)) - 1]
    quantidade = ler_numero("Quantidade (1 a 5): ", 1, 5)
    pontos_ganhos = postagens[tipo] * quantidade

    with conexao.cursor() as cursor:
        cursor.execute(
            "UPDATE usuario SET pontos = pontos + :1 WHERE id_usuario = :2",
            (pontos_ganhos, usuario["id"])
        )
        cursor.execute(
            "INSERT INTO historico (id_usuario, descricao) VALUES (:1, :2)",
            (usuario["id"], f"{quantidade}x {tipo}: +{pontos_ganhos} pontos")
        )
    conexao.commit()  # um unico commit: ou grava os dois, ou nenhum
    exportar_json(conexao)
    print(f"Voce ganhou {pontos_ganhos} pontos!")


def converter_pontos(conexao):
    usuario = buscar_usuario(conexao, input("Seu e-mail: "))
    if not usuario:
        print("Usuario nao encontrado.")
        return
    if usuario["pontos"] == 0:
        print("Voce nao possui pontos para converter.")
        return

    print(f"Cada ponto vale R$ {VALOR_POR_PONTO:.4f}.")
    try:
        usar = int(input("Quantos pontos deseja converter? "))
    except ValueError:
        print("Digite apenas numeros para a quantidade de pontos.")
        return

    if usar < 1 or usar > usuario["pontos"]:
        print("Quantidade de pontos invalida.")
        return

    valor = usar * VALOR_POR_PONTO
    with conexao.cursor() as cursor:
        cursor.execute(
            "UPDATE usuario SET pontos = pontos - :1 WHERE id_usuario = :2",
            (usar, usuario["id"])
        )
        cursor.execute(
            "INSERT INTO historico (id_usuario, descricao) VALUES (:1, :2)",
            (usuario["id"], f"Conversao: -{usar} pontos = R$ {valor:.2f}")
        )
    conexao.commit()
    exportar_json(conexao)
    print(f"Valor estimado: R$ {valor:.2f}")


def consultar_saldo(conexao):
    usuario = buscar_usuario(conexao, input("Seu e-mail: "))
    if not usuario:
        print("Usuario nao encontrado.")
        return

    valor = usuario["pontos"] * VALOR_POR_PONTO
    print(f"\nNome: {usuario['nome']}")
    print(f"Pontos: {usuario['pontos']}")
    print(f"Valor estimado: R$ {valor:.2f}")
    print("Historico:")
    with conexao.cursor() as cursor:
        cursor.execute(
            "SELECT descricao FROM historico WHERE id_usuario = :1 ORDER BY id_historico",
            (usuario["id"],)
        )
        for (descricao,) in cursor.fetchall():
            print("-", descricao)


# ---------------------------------------------------------
# MENUS
# ---------------------------------------------------------
def executar(acao, conexao):
    """Roda uma funcao e, se o Oracle der erro, desfaz a operacao (rollback)."""
    try:
        acao(conexao)
    except oracledb.Error as erro:
        conexao.rollback()
        print(f"Erro no banco de dados: {erro}")
    except OSError:
        print("Nao foi possivel gravar o arquivo JSON.")


def menu_usuarios(conexao):
    while True:
        print("\n1 - Cadastrar | 2 - Listar | 3 - Consultar")
        print("4 - Editar | 5 - Excluir | 0 - Voltar")
        opcao = input("Opcao: ")

        if opcao == "1":
            executar(cadastrar_usuario, conexao)
        elif opcao == "2":
            executar(listar_usuarios, conexao)
        elif opcao == "3":
            executar(consultar_usuario, conexao)
        elif opcao == "4":
            executar(editar_usuario, conexao)
        elif opcao == "5":
            executar(excluir_usuario, conexao)
        elif opcao == "0":
            break
        else:
            print("Opcao invalida.")


def menu(conexao):
    while True:
        print("\n===== SOUL UP =====")
        print("1 - Usuarios")
        print("2 - Registrar postagem")
        print("3 - Converter pontos")
        print("4 - Consultar saldo")
        print("5 - Exibir JSON")
        print("0 - Sair")
        opcao = input("Opcao: ")

        if opcao == "1":
            menu_usuarios(conexao)
        elif opcao == "2":
            executar(registrar_postagem, conexao)
        elif opcao == "3":
            executar(converter_pontos, conexao)
        elif opcao == "4":
            executar(consultar_saldo, conexao)
        elif opcao == "5":
            exibir_json()
        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opcao invalida.")


# ---------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------
try:
    conexao = conectar()
except oracledb.Error as erro:
    print(f"Nao foi possivel conectar ao Oracle: {erro}")
else:
    try:
        exportar_json(conexao)  # deixa o JSON sincronizado com o banco ao iniciar
        menu(conexao)
    finally:
        conexao.close()
