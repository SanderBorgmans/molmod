# -*- coding: utf-8 -*-
# MolMod is a collection of molecular modelling tools for python.
# Copyright (C) 2007 - 2010 Toon Verstraelen <Toon.Verstraelen@UGent.be>, Center
# for Molecular Modeling (CMM), Ghent University, Ghent, Belgium; all rights
# reserved unless otherwise stated.
#
# This file is part of MolMod.
#
# MolMod is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# MolMod is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --


from molmod.utils import *

import unittest, pickle, numpy


__all__ = ["UtilsTestCase"]


class Test(ReadOnly):
    a = ReadOnlyAttribute(none=False)
    b = ReadOnlyAttribute()

    def __init__(self, a, b=None):
        self.a = a
        self.b = b


class TypeCheckTest(ReadOnly):
    a = ReadOnlyAttribute(int)
    b = ReadOnlyAttribute(numpy.ndarray)
    c = ReadOnlyAttribute(numpy.ndarray, npdim=2)
    d = ReadOnlyAttribute(numpy.ndarray, npshape=(None,3))
    e = ReadOnlyAttribute(numpy.ndarray, npdtype=float)


class CustomCheckTest(ReadOnly):
    def check_b(self, b):
        if len(b) != self.a:
            raise TypeError()

    a = ReadOnlyAttribute(int, none=False)
    b = ReadOnlyAttribute(numpy.ndarray, check=check_b, npdim=1, npdtype=int)

    def __init__(self, a, b=None):
        self.a = a
        self.b = b

class UtilsTestCase(unittest.TestCase):
    def test_pickle_read_only1(self):
        test1 = Test(5)
        s = pickle.dumps(test1)
        test2 = pickle.loads(s)
        self.assertEqual(test1.a, test2.a)
        self.assertEqual(test1.b, None)
        self.assertEqual(test2.b, None)
        test1.b = "foo"
        self.assertEqual(test1.b, "foo")

    def test_pickle_read_only2(self):
        test1 = Test(5, 3)
        s = pickle.dumps(test1)
        test2 = pickle.loads(s)
        self.assertEqual(test1.a, test2.a)
        self.assertEqual(test1.b, test2.b)

    def check_type_error(self, fn, *args, **kwargs):
        try:
            test = fn(*args, **kwargs)
            self.fail("Should have raised a TypeError")
        except TypeError, e:
            #print e
            pass
        except Exception, e:
            self.fail("Should have raised a TypeError. Got %s" % e)

    def test_assign_none(self):
        self.check_type_error(Test, None)

    def test_copy_with(self):
        test1 = Test(5,4)
        test2 = test1.copy_with(a=2)
        assert(test2.a == 2)
        assert(test2.b == 4)

    def test_type_checking_correct(self):
        test = TypeCheckTest()
        test.a = 5
        test.b = numpy.array([5, 3])
        test.c = numpy.identity(2)
        test.d = numpy.array([[[1.2], [3.5], [10.0]], [[7.1], [0.1], [0.2]]])
        test.e = numpy.array([4.2, 3.1])

    def test_type_checking_wrong(self):
        test = TypeCheckTest()
        self.check_type_error(setattr, test, "a", "foo")
        self.check_type_error(setattr, test, "b", test)
        self.check_type_error(setattr, test, "c", numpy.array([2, 3]))
        self.check_type_error(setattr, test, "d", numpy.array([2, 3]))
        test.c = numpy.identity(2)
        test.d = numpy.array([[1.2, 3.5, 10.0], [7.1, 0.1, 0.2]])
        test.e = numpy.array([4.2, 3.1])

    def test_assign_list(self):
        self.check_type_error(Test, [4, 5])

    def test_custon_check_correct(self):
        test = CustomCheckTest(5)
        test.b = numpy.zeros(5, int)

    def test_custon_check_wrong(self):
        test = CustomCheckTest(5)
        self.check_type_error(setattr, test, "b", numpy.zeros(4, int))
