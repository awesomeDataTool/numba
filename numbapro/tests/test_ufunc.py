import logging
import unittest

import numpy as np

from numba import *
from numbapro.vectorize import *
from numbapro.vectorize.minivectorize import MiniVectorize

dtype = np.float32
a = np.arange(80, dtype=dtype).reshape(8, 10)
b = a.copy()
c = a.copy(order='F')
d = np.arange(16 * 20, dtype=dtype).reshape(16, 20)[::2, ::2]

def add(a, b):
    return a + b

def add_multiple_args(a, b, c, d):
    return a + b + c + d

def gufunc_add(a, b):
    result = 0.0
    for i in range(a.shape[0]):
        result += a[i] * b[i]

    return result


def ufunc_reduce(ufunc, arg):
    for i in range(arg.ndim):
        arg = ufunc.reduce(arg)
    return arg

vectorizers = [
    BasicVectorize,
    # ParallelVectorize,
    # StreamVectorize,
    # CudaVectorize,
    MiniVectorize,
    # GUFuncVectorize,
]

class TestUFuncs(unittest.TestCase):
    def _test_ufunc_attributes(self, cls, a, b, *args):
        "Test ufunc attributes"
        vectorizer = cls(add, *args)
        vectorizer.add(restype=f4, argtypes=[f4, f4])
        ufunc = vectorizer.build_ufunc()

        info = (cls, a.ndim)
        assert np.all(ufunc(a, b) == a + b), info
        assert ufunc_reduce(ufunc, a) == np.sum(a), info
        assert np.all(ufunc.accumulate(a) == np.add.accumulate(a)), info
        assert np.all(ufunc.outer(a, b) == np.add.outer(a, b)), info

    def _test_broadcasting(self, cls, a, b, c, d):
        "Test multiple args"
        vectorizer = cls(add_multiple_args)
        vectorizer.add(restype=f4, argtypes=[f4, f4, f4, f4])
        ufunc = vectorizer.build_ufunc()

        info = (cls, a.shape)
        assert np.all(ufunc(a, b, c, d) == a + b + c + d), info

    def test_ufunc_attributes(self):
        for v in vectorizers: # 1D
            self._test_ufunc_attributes(v, a[0], b[0])
        for v in vectorizers: # 2D
            self._test_ufunc_attributes(v, a, b)
        for v in vectorizers: # 3D
            self._test_ufunc_attributes(v, a[:, np.newaxis, :],
                                           b[np.newaxis, :, :])

    def test_broadcasting(self):
        for v in vectorizers: # 1D
            self._test_broadcasting(v, a[0], b[0], c[0], d[0])
        for v in vectorizers: # 2D
            self._test_broadcasting(v, a, b, c, d)
        for v in vectorizers: # 3D
            self._test_broadcasting(v, a[:, np.newaxis, :], b[np.newaxis, :, :],
                                       c[:, np.newaxis, :], d[np.newaxis, :, :])

    def test_implicit_broadcasting(self):
        for v in vectorizers:
            vectorizer = v(add)
            vectorizer.add(restype=f4, argtypes=[f4, f4])
            ufunc = vectorizer.build_ufunc()

            broadcasting_b = b[np.newaxis, :, np.newaxis, np.newaxis, :]
            assert np.all(ufunc(a, broadcasting_b) == a + broadcasting_b)

#    def test_gufunc(self):
#        "Test multiple args"
#        vectorizer = GUFuncVectorize(gufunc_add, "(m)(m)->()")
#        vectorizer.add(argtypes=[f[:], f[:]])
#        ufunc = vectorizer.build_ufunc()
#
#        a = np.arange(12 * 10, dtype=dtype).reshape(12, 10)
#        b = np.arange(12, dtype=dtype)
#        assert np.all(ufunc(a, b) == np.dot(a, b)), ufunc(a, b)


if __name__ == '__main__':
    # TestUFuncs('test_broadcasting').test_broadcasting()
    unittest.main()