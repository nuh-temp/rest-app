import collections
import importlib
import functools
import logging

import webapp2
from webapp2_extras import routes

class BaseHandler(webapp2.RequestHandler):
  """Wraps RequestHandler."""

  def __init__(self, *args, **kwargs):
    self._name = kwargs.pop('name', None)
    self._model_names = kwargs.pop('model_names', None)
    super(BaseHandler, self).__init__(*args, **kwargs)

  @property
  def name(self):
    return self._name

  @property
  def db(self):
    return 'DBConnection: %s' % list(self._model_names)


class BaseHandlerAdapter(webapp2.BaseHandlerAdapter):

  _model_names = None

  def __init__(self, handler, model_names=None):
    self._model_names = model_names
    self.handler = handler

  def __call__(self, request, response):
    # The handler only receives *args if no named variables are set.
    args, kwargs = request.route_args, request.route_kwargs
    if kwargs:
      args = ()

    # Inject handler object to handler
    return self.handler(
        BaseHandler(request, response,
                    name=self.handler.__name__,
                    model_names=self._model_names),
        *args, **kwargs)


class CustomRouter(webapp2.Router):
  _model_names = {}

  def add_models(self, handler_id, model_names):
    self._model_names[handler_id] = model_names

class WSGIApplication(webapp2.WSGIApplication):

  router_class = CustomRouter

  _METHODS = ['GET', 'POST', 'PUT', 'DELETE']

  def __init__(self, *args, **kwargs):
    super(WSGIApplication, self).__init__(*args, **kwargs)
    self.router.set_dispatcher(self.__class__.custom_dispatcher)
    self.router.set_adapter(self.__class__.custom_adapter)

  @staticmethod
  def custom_dispatcher(router, request, response):
    # logging.info('match_routes: %s', router.match_routes)
    # logging.info('build_routes: %s', router.build_routes)
    rv = router.default_dispatcher(request, response)
    if isinstance(rv, basestring):
      rv = webapp2.Response(rv)
    elif isinstance(rv, tuple):
      rv = webapp2.Response(*rv)

    return rv

  @staticmethod
  def custom_adapter(router, handler):
    model_names = router._model_names.get(id(handler), None)
    return BaseHandlerAdapter(handler, model_names=model_names)

  def InitHandlers(self, path, handlers):
    for h in handlers:
      importlib.import_module('%s.%s' % (path, h))

  def http_get(self, regex, models=None):
    return self.route(regex, methods=['GET'], models=models)

  def http_post(self, regex, models=None):
    return self.route(regex, methods=['POST'], models=models)

  def http_put(self, regex, models=None):
    return self.route(regex, methods=['PUT'], models=models)

  def http_delete(self, regex, models=None):
    return self.route(regex, methods=['DELETE'], models=models)

  def http_all(self, regex, models=None):
    return self.route(regex, methods=self._METHODS, models=models)

  def route(self, regex, methods=_METHODS, models=None):
    def wrapper(func):
      # logging.info('---> add (%s) route "%s" to %s', method, regex, func)

      url = ''.join([regex])

      if models:
        self.router.add_models(id(func), models)

      self.router.add(webapp2.Route(url, handler=func, methods=methods))
      if len(url) > 1:
        extra_url = '%s/' % url if url[-1] != '/' else url[:-1]
        self.router.add(webapp2.Route(extra_url, handler=func, methods=methods))
      return func
    return wrapper

app = WSGIApplication([], debug=True)
