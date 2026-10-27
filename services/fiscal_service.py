import requests
import streamlit as st
from datetime import datetime


def _obter_config():
    """Recupera as credenciais e aponta para o servidor unificado da Focus NFe."""
    conf = st.secrets.get("focusnfe", {})
    token = conf.get("token", "")
    # Os endpoints modernos (empresas e NFS-e Nacional /v2/nfsen) residem sempre em api.focusnfe.com.br
    base_url = "https://api.focusnfe.com.br"
    return token, base_url


def limpar_documento(doc):
    """Remove caracteres não numéricos."""
    if not doc:
        return ""
    return "".join(filter(str.isdigit, str(doc)))


def emitir_nfse(referencia, dados_nota):
    """
    Transmite a NFS-e Nacional pelo endpoint oficial /v2/nfsen.
    """
    token, base_url = _obter_config()
    cnpj_prestador = limpar_documento(dados_nota.get("cnpj_prestador"))
    tomador_doc = limpar_documento(dados_nota.get("tomador_documento", ""))
    cod_mun = str(dados_nota.get("codigo_municipio", "")).strip()

    # Estrutura padrão compatível com a NFS-e Nacional da Focus NFe
    payload = {
        "data_emissao": datetime.now().strftime("%Y-%m-%d"),
        "prestador": {
            "cnpj": cnpj_prestador,
            "codigo_municipio": cod_mun or "3300456"
        },
        "tomador": {
            "razao_social": dados_nota.get("tomador_nome", "Consumidor Final")
        },
        "servico": {
            "valor_servicos": float(dados_nota.get("valor_total", 0.0)),
            "discriminacao": dados_nota.get("descricao_servico", "Prestação de serviços"),
            "item_lista_servico": str(dados_nota.get("item_lista_servico") or "010701"),
            "aliquota": float(dados_nota.get("aliquota_iss", 0.0)),
            "iss_retido": False
        }
    }

    # Documento do tomador (CPF ou CNPJ)
    if len(tomador_doc) == 14:
        payload["tomador"]["cnpj"] = tomador_doc
    elif len(tomador_doc) == 11:
        payload["tomador"]["cpf"] = tomador_doc

    if dados_nota.get("tomador_email"):
        payload["tomador"]["email"] = dados_nota["tomador_email"]

    im_prestador = str(dados_nota.get("inscricao_municipal") or "").strip()
    if im_prestador:
        payload["prestador"]["inscricao_municipal"] = im_prestador

    # Rota nacional oficial
    url = f"{base_url}/v2/nfsen?ref={referencia}"
    resp = requests.post(url, json=payload, auth=(token, ""), timeout=25)

    if resp.status_code in [200, 201, 202]:
        return resp.json()
    else:
        raise Exception(f"Erro retornado pela Focus NFe: {resp.text}")


def consultar_nfse(referencia):
    """
    Consulta o processamento da NFS-e Nacional pelo endpoint /v2/nfsen.
    """
    token, base_url = _obter_config()
    url = f"{base_url}/v2/nfsen/{referencia}?completo=1"
    resp = requests.get(url, auth=(token, ""), timeout=15)
    if resp.status_code == 200:
        return resp.json()
    raise Exception(f"Erro ao consultar documento: {resp.text}")


def cadastrar_ou_atualizar_empresa(dados_empresa):
    """
    Cadastra ou atualiza o emitente na Focus NFe habilitando o ambiente nacional.
    """
    token, base_url = _obter_config()
    cnpj = limpar_documento(dados_empresa.get("cnpj"))

    payload = {
        "nome": dados_empresa.get("razao_social"),
        "nome_fantasia": dados_empresa.get("nome_fantasia") or dados_empresa.get("razao_social"),
        "cnpj": cnpj,
        "inscricao_municipal": str(dados_empresa.get("inscricao_municipal") or ""),
        "regime_tributario": int(dados_empresa.get("regime_tributario", 1)),
        "optante_simples_nacional": True,
        "habilita_nfsen": True,
        "habilita_nfsen_homologacao": True
    }

    if dados_empresa.get("email"):
        payload["email"] = dados_empresa["email"]
    if dados_empresa.get("telefone"):
        payload["telefone"] = dados_empresa["telefone"]

    url_put = f"{base_url}/v2/empresas/{cnpj}"
    resp = requests.put(url_put, json=payload, auth=(token, ""), timeout=15)

    if resp.status_code in [200, 201]:
        return resp.json()
    elif resp.status_code == 404:
        url_post = f"{base_url}/v2/empresas"
        resp_post = requests.post(url_post, json=payload, auth=(token, ""), timeout=15)
        if resp_post.status_code in [200, 201]:
            return resp_post.json()
        raise Exception(f"Erro ao cadastrar empresa na Focus NFe: {resp_post.text}")
    else:
        raise Exception(f"Falha na comunicação cadastral: {resp.text}")