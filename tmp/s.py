import logging
import sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

import mod1

model1_cls = mod1.factory('1')
obj1 = model1_cls('1')
cls_m1 = model1_cls.ClassEnv()
logging.info('model1_cls: %s, %s, %s', model1_cls, id(model1_cls), id(model1_cls._factory_env))
logging.info('(obj1) name: %s, env: %s, env.id: %s, _a: %s', obj1._name, obj1.env, id(obj1.env), obj1._a)
logging.info('cls_m1: %s, %s', cls_m1, id(cls_m1))

logging.info('########################')
model2_cls = mod1.factory('2')
obj2 = model2_cls('2')
cls_m2 = model2_cls.ClassEnv()
logging.info('model2_cls: %s, %s, %s', model2_cls, id(model2_cls), id(model2_cls._factory_env))
logging.info('(obj2) name: %s, env: %s, env.id: %s, _a: %s', obj2._name, obj2.env, id(obj2.env), obj2._a)
logging.info('cls_m2: %s, %s', cls_m2, id(cls_m2))
