import user

class Model:
    _name = 'base'
    def __init__(self):
        pass

    @property
    def name(self):
        return self._name

    @property
    def user(self):
        return user.GetUser()
