__author__ = 'William'

class TestClass():

    def __init__(self):
        self.dictionary = {'longname': {'long key': 'long output'}}

    @property
    def d(self):
        return self.dictionary

    @d.setter
    def d(self, value):
        self.dictionary = value

    @property
    def l(self):
        return self.d['longname']

    @l.setter
    def l(self, value):
        self.d['longname'] = value

    @property
    def lk(self):
        return self.l['long key']

    @lk.setter
    def lk(self, value):
        self.l['long key'] = value

r = TestClass()
r.d
r.d['l'] = 'o'
