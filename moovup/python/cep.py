import re 
import requests

URL_VIACEP = "https://viacep.com.br/ws/{cep}/json/"

def buscar_endereco(cep):
    cep = re.sub(r"\D", "", cep or "")

    if len(cep) != 8:
        raise ValueError("CEP com o valor invalido, e necessario 8 digitos")

    try:
        resposta = requests.get(URL_VIACEP.format(cep=cep), timeout=5)
        resposta.raise_for_status()
    except requests.RequestException:
        raise ValueError ("Nao foi possivel estabelecer uma conexao com a API. Tente novamente")

    endereco = resposta.json()
    if endereco.get("erro"):
        raise ValueError("CEP nao encontrado")

    return {
        "cep": endereco["cep"],
        "logradouro": endereco.get("logradouro", ""),
        "bairro": endereco.get("bairro", ""),
        "cidade": endereco.get("localidade", ""),
        "uf": endereco.get("uf", ""),
    }