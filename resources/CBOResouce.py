from flask import request, abort
from flask_restful import Resource, marshal

from sqlalchemy.exc import SQLAlchemyError

import requests
import os

from helpers.database import db
from helpers.logging import logger, log_exception

from models.CBO import cbo_fields, CBO

SOLR_QUERY_URL = os.getenv("SOLR_QUERY_URL")
SOLR_UPDATE_URL = os.getenv("SOLR_UPDATE_URL")

class CbosResouce(Resource):
    def get(self):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 100))
        search_query = request.args.get('q', "").strip()

        if search_query:
            logger.info(f"Busca Solr: '{search_query}'")
            try:
                # 2. Monta e executa a requisição GET para o Solr
                solr_params = {
                    'q': f'titulo:{search_query}',  # Busca no campo 'titulo'
                    'fl': 'cod_cbo, titulo',        # Retorna apenas estes campos
                    'wt': 'json'                    # Formato de resposta JSON
                }
                
                response = requests.get(SOLR_QUERY_URL, params=solr_params)
                response.raise_for_status()
                
                solr_data = response.json()
                solr_results = solr_data.get('response', {}).get('docs', [])
                
                # 3. Transforma o resultado do Solr para o formato da API
                cbos_results = []
                for doc in solr_results:
                    cbos_results.append({
                        'cod_cbo': doc['cod_cbo'],
                        'titulo': doc['titulo']
                    })
                
                logger.info(f"Solr retornou {len(cbos_results)} resultados para '{search_query}'")
                return marshal(cbos_results, cbo_fields), 200

            except requests.exceptions.RequestException as e:
                log_exception(f"Erro de conexão/requisição Solr: {e}")
                abort(503, description="Serviço de busca (Solr) indisponível.")
            except Exception:
                log_exception("Erro inesperado na busca Solr")
                abort(500, description="Ocorreu um erro inesperado na busca.")
        else:

            # Contagem total filtrada
            count_query = db.select(db.func.count()).select_from(CBO)
            total = db.session.execute(count_query).scalar()

            try:
                logger.info(f"Get - Todas as CBOs")
                cbos = db.session.execute(
                    db.select(CBO)
                    .order_by(CBO.titulo.asc())
                    .offset((page - 1) * per_page).limit(per_page)
                    ).scalars().all()

                if not cbos:
                    logger.warning(f"Nenhum CBO(Classificação Brasileira de Ocupações) encontrado.")
                    return {
                        "mensagem": "Nenhum CBO(Classificação Brasileira de Ocupações) encontrado.",
                        "cbos": [],
                        "total": 0
                    }, 404

                logger.info(f"CBOs retornadas com sucesso")
                return { "CBOs": marshal(cbos, cbo_fields), 
                        "page": page, 
                        "per_page": per_page, 
                        "total": total }, 200
        
            except SQLAlchemyError:
                log_exception("Exception SQLAlchemy ao buscar CBOs.")
                db.session.rollback()
                abort(500, description="Problema com o banco de dados.")
            except Exception:
                log_exception("Erro inesperado ao buscar CBOs")
                abort(500, description="Ocorreu um erro inesperado.")

    def post(self):
        logger.info("Post - CBO")
        cbo_data = request.get_json()

        try:
            nova_cbo = CBO(**cbo_data)

            db.session.add(nova_cbo)
            db.session.commit()
            
            try:
                doc_to_solr = [{
                    "id": str(nova_cbo.cod_cbo),
                    "cod_cbo": nova_cbo.cod_cbo,
                    "titulo": nova_cbo.titulo
                }]
                solr_response = requests.post(SOLR_UPDATE_URL, 
                                            json=doc_to_solr,
                                            headers={'Content-Type': 'application/json'})
                solr_response.raise_for_status()
                logger.info(f"CBO {nova_cbo.cod_cbo} adicionada ao Solr com sucesso")
            except requests.exceptions.RequestException as e:
                log_exception(f"Erro ao adicionar CBO {nova_cbo.cod_cbo} ao Solr: {e}")
                abort(503, description="Serviço de busca (Solr) indisponível.")
            logger.info(f"Nova CBO com codigo {nova_cbo.cod_cbo} cadastrada com sucesso")
            return marshal(nova_cbo, cbo_fields), 201
        
        except SQLAlchemyError:
            log_exception("Exception SQLAlchemy ao inserir nova CBO.")
            db.session.rollback()
            abort(500, description="Problema com o banco de dados.")
        except Exception:
            log_exception("Erro inesperado ao inserir nova CBO")
            abort(500, description="Ocorreu um erro inesperado.")

class CboResouce(Resource):
    def get(self, cod_cbo):
        logger.info(f"Get - CBO por código: {cod_cbo}")

        try:
            cbo = db.session.execute(
                db.select(CBO)
                .filter_by(cod_cbo=cod_cbo)
            ).scalar_one_or_none()

            if cbo is None:
                logger.warning(f"CBO com código {cod_cbo} não encontrada.")
                return {"mensagem": "CBO não encontrada."}, 404

            logger.info(f"CBO com código {cod_cbo} retornada com sucesso")            
            return marshal(cbo, cbo_fields), 200

        except SQLAlchemyError:
            log_exception("Exception SQLAlchemy ao buscar cbo por código.")
            db.session.rollback()
            abort(500, description="Problema com o banco de dados.")
        except Exception:
            log_exception("Erro inesperado ao buscar cbo")
            abort(500, description="Ocorreu um erro inesperado.")

    def put(self, cod_cbo):
        logger.info(f"Put - Tentativa de atualizar CBO com código: {cod_cbo}")
        cbo_data = request.get_json()

        try:
            cbo = db.session.execute(
                db.select(CBO)
                .filter_by(cod_cbo=cod_cbo)
            ).scalar_one_or_none()

            if cbo is None:
                logger.warning(f"CBO com código {cod_cbo} não encontrada para atualizar.")
                return {"mensagem": "CBO não encontrada."}, 404

            titulo_antigo = cbo.titulo
            dados_alterados = False

            for key, value in cbo_data.items():
                if hasattr(cbo, key):
                    valor_antigo = getattr(cbo, key)
                    if valor_antigo != value:
                        setattr(cbo, key, value)
                        dados_alterados = True
                        if key == 'titulo':
                            titulo_novo = value

            if not dados_alterados:
                logger.info(f"Nenhuma alteração detectada para CBO {cod_cbo}")
                return {"mensagem": "Nenhuma alteração necessária."}, 200

            db.session.commit()

            # Atualiza no Solr se o título foi alterado ou se houve alguma mudança
            try:
                # Prepara documento para atualização no Solr
                doc_to_solr = [{
                    "id": str(cod_cbo),
                    "cod_cbo": cod_cbo,
                    "titulo": titulo_novo if 'titulo_novo' in locals() else cbo.titulo
                }]
                
                solr_response = requests.post(SOLR_UPDATE_URL, 
                                            json=doc_to_solr,
                                            headers={'Content-Type': 'application/json'})
                solr_response.raise_for_status()
                logger.info(f"CBO {cod_cbo} atualizada no Solr com sucesso")
            except requests.exceptions.RequestException as e:
                log_exception(f"Erro ao atualizar CBO {cod_cbo} no Solr: {e}")
                abort(503, description="Serviço de busca (Solr) indisponível.")
            logger.info(f"CBO com código {cod_cbo} atualizada com sucesso.")
            return {"mensagem": "CBO atualizada com sucesso."}, 200
        
        except SQLAlchemyError:
            log_exception("Exception SQLAlchemy ao atualizar CBO.")
            db.session.rollback()
            abort(500, description="Problema com o banco de dados.")
        except Exception:
            log_exception(f"Erro inesperado ao atualizar CBO")
            abort(500, description="Ocorreu um erro inesperado.")

    def delete(self, cod_cbo):
        logger.info(f"Delete - Tentativa de deleção cbo com código: {cod_cbo}")

        try:
            cbo = db.session.execute(
                db.select(CBO)
                .filter_by(cod_cbo=cod_cbo)
            ).scalar_one_or_none()

            if cbo is None:
                logger.warning(f"CBO com código {cod_cbo} não encontrada para deleção.")
                return {"mensagem": "CBO não encontrada."}, 404
            
            db.session.delete(cbo)
            db.session.commit()

            # Remove do Solr após deletar do banco
            try:
                # Envia comando de delete para o Solr
                delete_doc = {
                    "delete": {"id": str(cod_cbo)}
                }
                
                solr_response = requests.post(SOLR_UPDATE_URL, 
                                            json=delete_doc,
                                            headers={'Content-Type': 'application/json'})
                solr_response.raise_for_status()
                logger.info(f"CBO {cod_cbo} removida do Solr com sucesso")
            except requests.exceptions.RequestException as e:
                log_exception(f"Erro ao remover CBO {cod_cbo} do Solr: {e}")
                abort(503, description="Serviço de busca (Solr) indisponível.")
            logger.info(f"CBO com código {cod_cbo} removida com sucesso.")
            return {"mensagem": "CBO removida com sucesso."}, 200
        
        except SQLAlchemyError:
            log_exception("Exception SQLAlchemy ao deletar CBO.")
            db.session.rollback()
            abort(500, description="Problema com o banco de dados.")
        except Exception:
            log_exception("Erro inesperado ao deletar CBO")
            abort(500, description="Ocorreu um erro inesperado.")