import streamlit as st
import requests
import re

def _obter_config():
    """Lê as credenciais da Focus NFe configuradas no secrets.toml."""
    cfg = st.secrets["focusnfe"]
    token = cfg["token"]
    ambiente = cfg.get("ambiente", "homologacao").lower()
    
    if ambiente == "producao":
        base_url = "https://api.focusnfe.com.br/v2"
    else:
        base_url = "https://homologacao.focusnfe.com.br/v2"
        
    return token, base_url

def limpar_documento(doc):
    """Remove pontuações e deixa apenas os dígitos de CPF ou CNPJ."""
    return re.sub(r"\D", "", str(doc or ""))

#Inicio do bloco
def cadastrar_ou_atualizar_empresa(dados_empresa):
    """
    Cadastra ou atualiza o emitente (MEI / Empresa) na Focus NFe.
    O endpoint de gestão de empresas reside sempre em api.focusnfe.com.br.
    """
    token, _ = _obter_config()
    cnpj = limpar_documento(dados_empresa.get("cnpj"))
    
    # URL da API de empresas é sempre na API principal
    url_base_empresas = "https://api.focusnfe.com.br/v2"
    
    payload = {
        "nome": dados_empresa.get("razao_social"),
        "nome_fantasia": dados_empresa.get("nome_fantasia") or dados_empresa.get("razao_social"),
        "cnpj": cnpj,
        "inscricao_municipal": str(dados_empresa.get("inscricao_municipal") or ""),
        "regime_tributario": int(dados_empresa.get("regime_tributario", 1)),
        "optante_simples_nacional": True,
        # Habilitação para o Padrão Nacional da NFS-e (MEI / Belford Roxo)
        "habilita_nfsen": True,
        "habilita_nfsen_homologacao": True
    }
    
    if dados_empresa.get("email"):
        payload["email"] = dados_empresa["email"]
    if dados_empresa.get("telefone"):
        payload["telefone"] = dados_empresa["telefone"]

    url_put = f"{url_base_empresas}/empresas/{cnpj}"
    resp = requests.put(url_put, json=payload, auth=(token, ""), timeout=15)
    
    if resp.status_code in [200, 201]:
        return resp.json()
    elif resp.status_code == 404:
        url_post = f"{url_base_empresas}/empresas"
        resp_post = requests.post(url_post, json=payload, auth=(token, ""), timeout=15)
        if resp_post.status_code in [200, 201]:
            return resp_post.json()
        raise Exception(f"Erro ao cadastrar empresa na Focus NFe: {resp_post.text}")
    else:
        raise Exception(f"Falha na comunicação cadastral: {resp.text}")
    
    #final do bloco

def emitir_nfse(referencia, dados_nota):
    """
    Envia a requisição de emissão de NFS-e para a Focus NFe.
    O parâmetro 'referencia' é o identificador único interno (ex: 'nfse_cli_1_102').
    """
    token, base_url = _obter_config()
    doc_tomador = limpar_documento(dados_nota.get("tomador_documento"))
    cnpj_prestador = limpar_documento(dados_nota.get("cnpj_prestador"))
    
    payload = {
        "data_emissao": dados_nota.get("data_emissao"),
        "prestador": {
            "cnpj": cnpj_prestador,
            "inscricao_municipal": str(dados_nota.get("inscricao_municipal") or ""),
            "codigo_municipio": str(dados_nota.get("codigo_municipio") or "")
        },
        "tomador": {
            "razao_social": dados_nota.get("tomador_nome"),
            "email": dados_nota.get("tomador_email", "")
        },
        "servico": {
            "valor_servicos": float(dados_nota.get("valor_total", 0.0)),
            "discriminacao": dados_nota.get("descricao_servico", ""),
            "item_lista_servico": str(dados_nota.get("item_lista_servico", "010701")),
            "aliquota": float(dados_nota.get("aliquota_iss", 0.0)),
            "iss_retido": False
        }
    }
    
    # Define se o tomador é pessoa física ou jurídica
    if len(doc_tomador) == 14:
        payload["tomador"]["cnpj"] = doc_tomador
    else:
        payload["tomador"]["cpf"] = doc_tomador

    # Emissão assíncrona da Focus NFe com referência única
    url = f"{base_url}/nfse?ref={referencia}"
    resp = requests.post(url, json=payload, auth=(token, ""), timeout=20)
    
    if resp.status_code in [200, 202]:
        return resp.json()
    else:
        raise Exception(f"Erro retornado pela Focus NFe: {resp.text}")

def consultar_status_nfse(referencia):
    """
    Consulta o estado de processamento de uma NFS-e a partir da sua referência.
    Retorna o status atual ('autorizado', 'processando_autorizacao', 'erro_autorizacao')
    e os links diretos do PDF (Danfe) e XML.
    """
    token, base_url = _obter_config()
    url = f"{base_url}/nfse/{referencia}?completo=1"
    
    resp = requests.get(url, auth=(token, ""), timeout=15)
    if resp.status_code == 200:
        return resp.json()
    return None