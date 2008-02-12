# MolMod is a collection of molecular modelling tools for python.
# Copyright (C) 2007 Toon Verstraelen <Toon.Verstraelen@UGent.be>
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
# Contact information:
#
# Supervisors
#
# Prof. Dr. Michel Waroquier and Prof. Dr. Ir. Veronique Van Speybroeck
#
# Center for Molecular Modeling
# Ghent University
# Proeftuinstraat 86, B-9000 GENT - BELGIUM
# Tel: +32 9 264 65 59
# Fax: +32 9 264 65 60
# Email: Michel.Waroquier@UGent.be
# Email: Veronique.VanSpeybroeck@UGent.be
#
# Author
#
# Ir. Toon Verstraelen
# Center for Molecular Modeling
# Ghent University
# Proeftuinstraat 86, B-9000 GENT - BELGIUM
# Tel: +32 9 264 65 56
# Email: Toon.Verstraelen@UGent.be
#
# --


from molmod.io.cp2k import *
from molmod.units import *

import numpy, unittest


__all__ = ["CP2KTestCase"]


class CP2KTestCase(unittest.TestCase):
    def test_cell_reader(self):
        cr = CellReader("input/md.cell")
        a = numpy.array(list(cr))/angstrom
        self.assertAlmostEqual(a[0,0,0], 20.0, 5)
        self.assertAlmostEqual(a[1,0,0], 19.9997567998, 5)
        self.assertAlmostEqual(a[1,1,0], 0.0, 5)
        self.assertAlmostEqual(a[1,1,1], 19.9997567998, 5)

    def test_input_file(self):
        cp2k_input = InputFile.read_from_file("input/water_md.inp")
        self.assert_(cp2k_input._consistent())

        # test that the read_from_file works
        self.assertEqual(cp2k_input["FORCE_EVAL"]["METHOD"].value, "Quickstep")
        self.assert_(cp2k_input._consistent())
        self.assertEqual(cp2k_input["MOTION"]["MD"]["ENSEMBLE"].value, "NVE")
        self.assert_(cp2k_input._consistent())

        # test the __getitem__, __setitem__ and __delitem__
        del cp2k_input["MOTION"]["MD"]["ENSEMBLE"]
        self.assert_(cp2k_input._consistent())
        try:
            print cp2k_input["MOTION"]["MD"]["ENSEMBLE"].value
            self.fail("Keyword ENSEMBLE should no longer exist.")
        except KeyError:
            pass

        cp2k_input["MOTION"]["MD"]["ENSEMBLE"] = Keyword("ENSEMBLE", "NVE")
        self.assert_(cp2k_input._consistent())
        self.assertEqual(cp2k_input["MOTION"]["MD"]["ENSEMBLE"].value, "NVE")

        try:
            cp2k_input["MOTION"]["MD"]["ENSEMBLE"] = Keyword("JOS", "NVE")
            self.fail("Keyword should have the correct name.")
        except KeyError:
            pass

        try:
            cp2k_input["MOTION"]["MD"]["ENSEMBLE"] = [Keyword("ENSEMBLE", "NVE"), Keyword("JOS", "NVE")]
            self.fail("Keyword should have the correct name.")
        except KeyError:
            pass

        cp2k_input["MOTION"]["MD"]["ENSEMBLE"] = [Keyword("ENSEMBLE", "NVE"), Keyword("ENSEMBLE", "NVT")]
        self.assert_(cp2k_input._consistent())
        cp2k_input["MOTION"]["MD"]["ENSEMBLE", 0] = Keyword("ENSEMBLE", "NVE")
        self.assert_(cp2k_input._consistent())

        self.assertEqual(len(cp2k_input["MOTION"]["MD"]["ENSEMBLE"]), 2)
        l = cp2k_input["MOTION"]["MD"]["ENSEMBLE"]
        self.assertEqual(l[0].value, "NVE")
        self.assertEqual(l[1].value, "NVT")

        del cp2k_input["MOTION"]["MD"]["ENSEMBLE", 0]
        self.assert_(cp2k_input._consistent())
        self.assertEqual(cp2k_input["MOTION"]["MD"]["ENSEMBLE"].value, "NVT")

        # test __len__
        self.assertEqual(len(cp2k_input), 3)
        self.assertEqual(len(cp2k_input["MOTION"]["MD"]), 5)
        cp2k_input["MOTION"]["MD"]["ENSEMBLE"] = [Keyword("ENSEMBLE", "NVE"), Keyword("ENSEMBLE", "NVT")]
        self.assert_(cp2k_input._consistent())
        self.assertEqual(len(cp2k_input["MOTION"]["MD"]), 6)
        del cp2k_input["MOTION"]["MD"]["ENSEMBLE", 1]
        self.assert_(cp2k_input._consistent())

        # test creating new parts
        nose = Section("NOSE", [
            Keyword("LENGTH", "3"),
            Keyword("TIMECON", "10.0")
        ])
        self.assert_(nose._consistent())

        # test append
        cp2k_input["MOTION"]["MD"].append(nose)
        self.assert_(cp2k_input._consistent())
        self.assertEqual(cp2k_input["MOTION"]["MD"]["NOSE"]["LENGTH"].value, "3")

        # test dump, load consistency, part 1: dump a file, load it again, should be the same
        cp2k_input.write_to_file("output/water_md.inp")
        cp2k_input_check = InputFile.read_from_file("output/water_md.inp")
        self.assert_(cp2k_input_check._consistent())
        self.assertEqual(cp2k_input, cp2k_input_check)

        # test dump-load consistency, part 2: no reordering of sections and keywords should be allowed
        cp2k_input = InputFile.read_from_file("input/water_md.inp")
        cp2k_input.write_to_file("output/water_md.inp")
        f1 = file("input/water_md.inp")
        f2 = file("output/water_md.inp")
        for line1, line2 in zip(f1, f2):
            self.assertEqual(line1, line2)
        f1.close()
        f2.close()




