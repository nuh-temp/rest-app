import logging
import inspect
import collections

Env = collections.namedtuple('Env', ['name'])

class BaseModel(object):
  _factory_env = None
  _a = None


class MyModel(BaseModel):
  # logging.info('--m1--> MyModel real class init: factory_env: %s, id: %s', f, id(f))

  _a = []
  def __init__(self, name):
    logging.info('--m1--> !!!! run __init__: %s', name)
    self._type = 'model'
    self._name = name

  @property
  def env(self):
    return self._factory_env

  @classmethod
  def ClassEnv(cls):
    return cls._factory_env or Env('NEW')


def factory(i):

  # factory_env = Env(i)
  # logging.info('--m1--> init factory: %s, factory_env: %s, factory_env_id: %s', i, factory_env, id(factory_env))

  CopyOfModel = type('MyModel', MyModel.__bases__, dict(MyModel.__dict__))
  CopyOfModel._factory_env = Env(i)
  CopyOfModel._a.append(i)
  return CopyOfModel

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
