# setup_solr.py
import requests
import time
import os

SOLR_API_URL = os.getenv("SOLR_HOST")
CORE_NAME = "cbo_core"
SCHEMA_ENDPOINT = f"{SOLR_API_URL}/{CORE_NAME}/schema"

def wait_for_solr():
    """Espera o Solr estar online e o core 'cbo_core' estar pronto."""
    print("Aguardando o Solr ficar disponível...")
    while True:
        try:
            response = requests.get(f"{SOLR_API_URL}/admin/cores?action=STATUS&core={CORE_NAME}")
            if response.status_code == 200 and CORE_NAME in response.json().get('status', {}):
                print(f"Solr e Core '{CORE_NAME}' estão prontos.")
                return
        except requests.exceptions.ConnectionError:
            pass # Solr ainda não respondeu, espera mais um pouco
        time.sleep(5)

def configure_solr_schema():
    """Adiciona/modifica os campos necessários no schema."""
    
    # 1. Comando para adicionar o campo 'cod_cbo' (armazenado, int, não indexado para busca de texto)
    # Na verdade, como usamos 'id' para a chave, e 'cod_cbo' para a busca, vamos focar em 'titulo'.
    
    # 2. Comando para adicionar o campo 'titulo' como text_pt (text-searchable, tokenizado para português)
    add_field_command = {
        "add-field": {
            "name": "titulo",
            "type": "text_pt", # Usa o analisador de texto para português
            "stored": True,     # O valor será retornado na busca
            "indexed": True     # O valor será usado no índice invertido
        }
    }

    try:
        response = requests.post(
            SCHEMA_ENDPOINT,
            json=add_field_command,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        print(f"Campo 'titulo' configurado com sucesso. Status: {response.json().get('responseHeader', {}).get('status')}")
    except requests.exceptions.HTTPError as e:
        # Se o campo já existir, Solr retorna 400. Isso é OK.
        if "already exists" in response.text:
            print("Campo 'titulo' já existe. Continuando.")
        else:
            print(f"ERRO ao configurar o campo 'titulo': {e}")
            print(response.text)
            
if __name__ == "__main__":
    wait_for_solr()
    configure_solr_schema()