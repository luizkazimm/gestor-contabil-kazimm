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

#Inicio do BLOCO
def emitir_nfse(referencia, dados_nota):
    """
    Transmite a Declaração de Prestação de Serviços (DPS) pelo endpoint nacional /v2/nfsen.
    """
    token, base_url = _obter_config()
    cnpj_prestador = limpar_documento(dados_nota.get("cnpj_prestador"))
    tomador_doc = limpar_documento(dados_nota.get("tomador_documento", ""))
    cod_mun = str(dados_nota.get("codigo_municipio", "")).strip()

    # Payload estruturado para o padrão NFS-e Nacional (/v2/nfsen)
    payload = {
        "data_emissao": datetime.now().strftime("%Y-%m-%dT%H:%M:%S-03:00"),
        "data_competencia": datetime.now().strftime("%Y-%m-%d"),
        "codigo_municipio_emissora": int(cod_mun) if cod_mun.isdigit() else 3300456,
        "codigo_municipio_prestacao": int(cod_mun) if cod_mun.isdigit() else 3300456,
        "cnpj_prestador": cnpj_prestador,
        "codigo_opcao_simples_nacional": 1,  # 1 = MEI optante pelo Simples Nacional
        "regime_especial_tributacao": 0,       # 0 = Nenhum
        "codigo_tributacao_nacional_iss": str(dados_nota.get("item_lista_servico") or "010701"),
        "descricao_servico": dados_nota.get("descricao_servico", "Prestação de serviços"),
        "valor_servico": float(dados_nota.get("valor_total", 0.0)),
        "tributacao_iss": 1                    # 1 = Tributável no município
    }

    # Vincula tomador (CPF ou CNPJ)
    if len(tomador_doc) == 14:
        payload["cnpj_tomador"] = tomador_doc
    elif len(tomador_doc) == 11:
        payload["cpf_tomador"] = tomador_doc

    if dados_nota.get("tomador_nome"):
        payload["razao_social_tomador"] = dados_nota["tomador_nome"]

    # Inscrição municipal apenas se existir e estiver cadastrada no emissor
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
    Consulta o status de processamento da NFS-e Nacional pelo endpoint /v2/nfsen.
    """
    token, base_url = _obter_config()
    url = f"{base_url}/v2/nfsen/{referencia}?completo=1"
    
    resp = requests.get(url, auth=(token, ""), timeout=15)
    if resp.status_code == 200:
        return resp.json()
    raise Exception(f"Erro ao consultar documento: {resp.text}")
# FIM DO BLOCO

    
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