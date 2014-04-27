import logging
import inspect
import collections

Env = collections.namedtuple('Env', ['name'])

class BaseModel(object):
  _factory_env = None
  pass


def factory(i):

  factory_env = Env(i)
  logging.info('--m1--> init factory: %s, factory_env: %s, factory_env_id: %s', i, factory_env, id(factory_env))

  def get(f):
    logging.info('--m1--> get: %s', f)
    class MyModel(BaseModel):
      logging.info('--m1--> MyModel real class init: %s, factory_env: %s, id: %s', i, f, id(f))
      _factory_env = f
      def __init__(self, name):
        logging.info('--m1--> !!!! run __init__: %s', name)
        self._type = 'model'
        self._name = name

      @property
      def env(self):
        return self._factory_env

      @classmethod
      def ClassEnv(cls):
        return factory_env

    return MyModel
  return get(factory_env)

# add shortcut for Factory.Env to GetEnv class variable
# for name in dir(Factory):
#   if name.startswith('__'):
#     continue

#   child = getattr(Factory, name)

#   if not inspect.isclass(child):
#     continue
#   parents = inspect.getmro(child)
#   # logging.info('=====> name4: %s, %s, %s', name, parents, bool(BaseModel in parents))
#   if BaseModel in parents:
#     child.GetEnv = Factory.Env
