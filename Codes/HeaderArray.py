import numpy as np


class HeaderArray(np.ndarray):

    def __new__(cls, input_array, header={}):
        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        obj = np.asarray(input_array).view(cls)
        # add the new attribute to the created instance
        obj.header = header
        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        # reset the attribute from passed original object
        self.header = getattr(obj, 'header', None)
        # We do not need to return anything
