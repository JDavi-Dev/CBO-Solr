import requests
import time
import os

CORE_NAME = os.getenv("CORE_NAME")
SCHEMA_ENDPOINT = os.getenv("SCHEMA_ENDPOINT")
STATUS_SOLR = os.getenv("STATUS_SOLR")

def wait_for_solr():
    """Espera o Solr estar online e o core 'cbo_core' estar pronto."""
    print("Aguardando o Solr ficar disponível...")
    while True:
        try:
            response = requests.get(STATUS_SOLR)
            if response.status_code == 200 and CORE_NAME in response.json().get('status', {}):
                print(f"Solr e Core '{CORE_NAME}' estão prontos.")
                return
        except requests.exceptions.ConnectionError:
            pass # Solr ainda não respondeu, espera mais um pouco
        time.sleep(5)

def configure_solr_schema():
    """Adiciona/modifica os campos necessários no schema."""
    
    # Lista de campos a serem configurados: '' e 
    fields_to_configure = [
        {
            "name": "cod_cbo",
            "type": "pint",    # Tipo inteiro (pint = primitive int)
            "stored": True,    # O valor será retornado na busca
            "indexed": True    # O valor será usado no índice invertido
        },
        {
            "name": "titulo",
            "type": "text_pt", # Usa o analisador de texto para português
            "stored": True,     # O valor será retornado na busca
            "indexed": True     # O valor será usado no índice invertido
        }
    ]

    for field_config in fields_to_configure:
        add_field_command = {"add-field": field_config}
        field_name = field_config["name"]
        
        try:
            response = requests.post(
                SCHEMA_ENDPOINT,
                json=add_field_command,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            print(f"Campo '{field_name}' configurado com sucesso. Status: {response.json().get('responseHeader', {}).get('status')}")
        except requests.exceptions.HTTPError as e:
            # Se o campo já existir, Solr retorna 400. Isso é OK.
            if "already exists" in response.text:
                print(f"Campo '{field_name}' já existe. Continuando.")
            else:
                print(f"ERRO ao configurar o campo '{field_name}': {e}")
                print(response.text)
            
if __name__ == "__main__":
    wait_for_solr()
    configure_solr_schema()