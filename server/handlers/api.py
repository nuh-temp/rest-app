import logging
from server.main import app

@app.http_get('/api/<req_id:(\d+)>')
def GetApi(handler, req_id=None):
  logging.info('DB: %s', handler.db)
  return 'GetApi: %s' % req_id

@app.http_get('/api/by_id/<req_id:(\d+)>/', models=('m1', 'm2'))
def GetApiById(handler, req_id=None):
  logging.info('DB: %s', handler.db)
  return 'GetApiById: %s, %s' % (req_id, handler.name)

@app.http_post('/api')
def PostApi(handler):
    return 'api!'

@app.http_get('/api/<action:[^/]+>')
def GetApiAction(handler, action=None):
  # logging.info('---> handler: %s', handler)
  # logging.info('---> request: %s', handler.request)
  return 'GetApiAction: %s' % action
