from helpers.application import app, api
from helpers.CORS import cors

# from resources.IndexResouce import IndexResource

from resources.CBOResouce import CbosResouce, CboResouce

cors.init_app(app)

# api.add_resource(IndexResource, '/')

api.add_resource(CbosResouce, '/cbos')
api.add_resource(CboResouce, '/cbo/<int:cod_cbo>')