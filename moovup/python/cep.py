import re 
import requests

URL_VIACEP = "https://viacep.com.br/ws/{cep}/json/"

def buscar_endereco(cep):
    cep = re.sub(r"\D", "", cep or "")

    if len(cep) != 8:
        raise ValueError("CEP com o valor invalido, e necessario 8 digitos")

