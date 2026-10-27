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
    Transmite a Declaração de Prestação de Serviços (DPS) pelo endpoint nacional /v2/nfsen.
    """
    token, base_url = _obter_config()

    cnpj_bruto = (
        dados_nota.get("cnpj_prestador")
        or dados_nota.get("cnpj")
        or dados_nota.get("prestador_cnpj")
        or ""
    )
    cnpj_prestador = limpar_documento(cnpj_bruto)
    tomador_doc = limpar_documento(dados_nota.get("tomador_documento", ""))
    cod_mun = str(dados_nota.get("codigo_municipio", "")).strip()

    if not cnpj_prestador:
        raise Exception(
            "O CNPJ do PRESTADOR (sua empresa) não foi encontrado. "
            "Acesse a aba 'Configuração Fiscal' e confirme se o seu CNPJ está salvo."
        )

    cod_mun_int = int(cod_mun) if cod_mun.isdigit() else 3300456

# Payload estruturado para o endpoint /v2/nfsen com data e hora completas (dhEmi)
    agora = datetime.now()

    # Enquadramento Simples Nacional: 1 = Não optante | 2 = MEI | 3 = ME/EPP
    opcao_simples = int(dados_nota.get("regime_tributario") or 2)
    codigo_simples_nacional = 2 if opcao_simples == 1 else opcao_simples

    payload = {
        "cnpj_prestador": cnpj_prestador,
        "codigo_municipio_emissora": cod_mun_int,
        "codigo_municipio_prestacao": cod_mun_int,
        "codigo_municipio_incidencia": cod_mun_int,
        "data_emissao": agora.strftime("%Y-%m-%dT%H:%M:%S-03:00"),
        "data_competencia": agora.strftime("%Y-%m-%d"),
        "codigo_opcao_simples_nacional": codigo_simples_nacional,
        "regime_especial_tributacao": 0,
        "codigo_tributacao_nacional_iss": str(dados_nota.get("item_lista_servico") or "010701"),
        "descricao_servico": dados_nota.get("descricao_servico", "Prestação de serviços"),
        "valor_servico": float(dados_nota.get("valor_total", 0.0)),
        "aliquota": float(dados_nota.get("aliquota_iss", 0.0)),
        "tributacao_iss": 1,
        "iss_retido": False,
        "tipo_retencao_iss": 1
    }
    
    # Dados do Tomador
    if len(tomador_doc) == 14:
        payload["cnpj_tomador"] = tomador_doc
    elif len(tomador_doc) == 11:
        payload["cpf_tomador"] = tomador_doc

    if dados_nota.get("tomador_nome"):
        payload["razao_social_tomador"] = dados_nota["tomador_nome"]

    if dados_nota.get("tomador_email"):
        payload["email_tomador"] = dados_nota["tomador_email"]

    im_prestador = str(dados_nota.get("inscricao_municipal") or "").strip()
    if im_prestador:
        payload["inscricao_municipal_prestador"] = im_prestador

    # Endpoint oficial da NFS-e Nacional
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
# Alias para compatibilidade com o Gestor Fiscal
consultar_status_nfse = consultar_nfse

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
        # Habilitações para NFS-e Nacional (Homologação e Produção)
        "habilita_nfsen": True,
        "habilita_nfsen_homologacao": True,
        "habilita_nfsen_producao": True
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