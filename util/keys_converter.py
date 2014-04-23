import json
import sys

current_module = sys.modules[__name__]

class Foo(object):
    def __init__(self, props):
        self._props = props

    def dump(self):
        return self._props

class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Foo):
            return dict(props=obj.dump(), __model='Foo')
        return super(MyEncoder, self).default(obj)

data = json.dumps({
    'myParam1': 1,
    'canView': True,
    'theArray': ['aaDf', 1, None],
    'myClass': Foo({'classProp1': 'aaaa'})
}, cls=MyEncoder)


def from_camel_case(obj):
    print 'obj: %s' % obj
    for key in obj.keys():
        new_key = []
        for idx, char in enumerate(key):
            if not char.istitle():
                new_key.append(char)
                continue
            new_key.append('_%s' % char.lower() if idx > 0 else char.lower())
        new_key = ''.join(new_key)
        if new_key != key:
            obj[new_key] = obj[key]
            del obj[key]
    # if '__model' in obj:
    #     cls = getattr(current_module, '__model')
    #     obj = cls(obj.props)
    return obj

def remove_dot_key(obj):
    for key in obj.keys():
        new_key = key.replace(".","")
        if new_key != key:
            obj[new_key] = obj[key]
            del obj[key]
    return obj

new_json = json.loads(data, object_hook=from_camel_case)
print new_json