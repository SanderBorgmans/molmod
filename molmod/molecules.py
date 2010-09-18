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
"""Data structure for molecular geometries"""


from molmod.periodic import periodic
from molmod.units import angstrom
from molmod.utils import cached, ReadOnly, ReadOnlyAttribute
from molmod.molecular_graphs import MolecularGraph
from molmod.unit_cells import UnitCell
from molmod.transformations import fit_rmsd
from molmod.symmetry import compute_rotsym

from StringIO import StringIO

import numpy


__all__ = ["Molecule"]


class Molecule(ReadOnly):
    """Extensible datastructure for molecular geometries

       Most attributes of the molecule object are treated as constants. If you
       want to modify the molecular geometry, just create a modified molecule
       object. This facilitates the caching of derived quantities such as the
       distance matrices, while it imposes a cleaner coding style without
       a signifacant computational overhead.
    """
    def check_coordinates(self, coordinates):
        if len(coordinates) != self.size:
            raise TypeError("The number of coordinates does not match the "
                "length of the atomic numbers array.")

    def check_masses(self, masses):
        if len(masses) != self.size:
            raise TypeError("The number of masses does not match the length of "
                "the atomic numbers array.")

    def check_graph(self, graph):
        if graph.num_vertices != self.size:
            raise TypeError("The number of vertices in the graph does not "
                "match the length of the atomic numbers array.")
        # In practice these are typically the same arrays using the same piece
        # of memory. Just checking to be sure.
        if (self.numbers != graph.numbers).any():
            raise TypeError("The atomic numbers in the graph do not match the "
                "atomic numbers in the molecule.")

    def check_symbols(self, symbols):
        if len(symbols) != self.size:
            raise TypeError("The number of symbols in the graph does not "
                "match the length of the atomic numbers array.")
        for symbol in symbols:
            if not isinstance(symbol, basestring):
                raise TypeError("All symbols must be strings.")

    numbers = ReadOnlyAttribute(numpy.ndarray, none=False, npdim=1, npdtype=int)
    coordinates = ReadOnlyAttribute(numpy.ndarray, npdim=2, npshape=(None,3),
        npdtype=float, check=check_coordinates)
    title = ReadOnlyAttribute(basestring)
    masses = ReadOnlyAttribute(numpy.ndarray, npdim=1, npdtype=float,
        check=check_masses)
    graph = ReadOnlyAttribute(MolecularGraph, check=check_graph)
    symbols = ReadOnlyAttribute(tuple, check_symbols)
    unit_cell = ReadOnlyAttribute(UnitCell)

    def __init__(self, numbers, coordinates=None, title=None, masses=None, graph=None, symbols=None, unit_cell=None):
        """
           Mandatory arguments:
            | ``numbers``  --  numpy array (1D, N elements) with the atomic numbers

           Optional keyword arguments:
            | ``coordinates``  --  numpy array (2D, Nx3 elements) Cartesian coordinates
            | ``title``  --  a string with the name of the molecule
            | ``massess``  --  a numpy array with atomic masses in atomic units
            | ``graph``  --  a MolecularGraph instance
            | ``symbols``  --  atomic elements or force-field atom-types
            | ``unit_cell``  --  the unit cell in case the system is periodic
        """
        self.numbers = numbers
        self.coordinates = coordinates
        self.title = title
        self.masses = masses
        self.graph = graph
        self.symbols = symbols
        self.unit_cell = unit_cell

    @classmethod
    def from_file(cls, filename):
        """Construct a molecule object read from the given file

           The file format is inferred from the extensions. Currently supported
           formats are: ``*.cml``, ``*.fchk``, ``*.pdb``, ``*.sdf``, ``*.xyz``

           If a file contains more than one molecule, only the first one is
           read.

           Argument:
            | ``filename``  --  the name of the file containing the molecule

           Example usage::

             >>> mol = Molecule.from_file("foo.xyz")
        """
        # TODO: many different API's to load files. brrr...
        if filename.endswith(".cml"):
            from molmod.io import load_cml
            return load_cml(filename)[0]
        elif filename.endswith(".fchk"):
            from molmod.io import FCHKFile
            fchk = FCHKFile(filename, field_labels=[])
            return fchk.molecule
        elif filename.endswith(".pdb"):
            from molmod.io import load_pdb
            return load_pdb(filename)
        elif filename.endswith(".sdf"):
            from molmod.io import SDFReader
            return SDFReader(filename).next()
        elif filename.endswith(".xyz"):
            from molmod.io import XYZReader
            xyz_reader = XYZReader(filename)
            title, coordinates = xyz_reader.next()
            return Molecule(xyz_reader.numbers, coordinates, title, symbols=xyz_reader.symbols)
        else:
            raise ValueError("Could not determine file format for %s." % filename)

    size = property(lambda self: self.numbers.shape[0])

    @cached
    def distance_matrix(self):
        """The matrix with all atom pair distances"""
        from molmod.ext import molecules_distance_matrix
        return molecules_distance_matrix(self.coordinates)

    @cached
    def mass(self):
        """The total mass of the molecule"""
        return self.masses.sum()

    @cached
    def com(self):
        """The center of mass of the molecule"""
        return (self.coordinates*self.masses.reshape((-1,1))).sum(axis=0)/self.mass

    @cached
    def inertia_tensor(self):
        """The intertia tensor of the molecule"""
        result = numpy.zeros((3,3), float)
        for i in xrange(self.size):
            r = self.coordinates[i] - self.com
            # the diagonal term
            result.ravel()[::4] += self.masses[i]*(r**2).sum()
            # the outer product term
            result -= self.masses[i]*numpy.outer(r,r)
        return result

    @cached
    def chemical_formula(self):
        """The chemical formula of the molecule"""
        counts = {}
        for number in self.numbers:
            counts[number] = counts.get(number, 0)+1
        items = []
        for number, count in sorted(counts.iteritems(), reverse=True):
            if count == 1:
                items.append(periodic[number].symbol)
            else:
                items.append("%s%i" % (periodic[number].symbol, count))
        return "".join(items)

    def set_default_masses(self):
        """Set self.masses based on self.numbers"""
        self.masses = numpy.array([periodic[n].mass for n in self.numbers])

    def set_default_graph(self):
        """Set self.graph to the default graph.

           This method is equivalent to::

              mol.graph = MolecularGraph.from_geometry(mol)

           with the default options, and only works if the graph object is not
           present yet.
           See :meth:`molmod.molecular_graphs.MolecularGraph.from_geometry`
           for more fine-grained control over the assignment of bonds.
        """
        self.graph = MolecularGraph.from_geometry(self)

    def set_default_symbols(self):
        """Set self.symbols based on self.numbers"""
        self.symbols = tuple(periodic[n].symbol for n in self.numbers)

    def write_to_file(self, filename):
        """Write the molecule geometry to a file

           The file format is inferred from the extensions. Currently supported
           formats are: ``*.xyz``, ``*.cml``

           Argument:
            | ``filename``  --  a filename
        """
        # TODO: give all file format writers the same API
        if filename.endswith('.cml'):
            from molmod.io import dump_cml
            dump_cml(filename, [self])
        elif filename.endswith('.xyz'):
            from molmod.io import XYZWriter
            symbols = []
            for n in self.numbers:
                atom = periodic[n]
                if atom is None:
                    symbols.append("X")
                else:
                    symbols.append(atom.symbol)
            xyz_writer = XYZWriter(filename, symbols)
            xyz_writer.dump(self.title, self.coordinates)
            del xyz_writer
        else:
            raise ValueError("Could not determine file format for %s." % filename)

    def rmsd(self, other):
        """Compute the RMSD between two molecules

           Arguments:
            | ``other``  --  Another molecule with the same atom numbers

           Return values:
            | ``transformation``  --  the transformation that brings 'self' into
                                  overlap with 'other'
            | ``other_trans``  --  the transformed coordinates of geometry 'other'
            | ``rmsd``  --  the rmsd of the distances between corresponding atoms in
                            'self' and 'other'

           Make sure the atoms in `self` and `other` are in the same order.

           Usage::

             >>> print molecule1.rmsd(molecule2)[2]/angstrom
        """
        if self.numbers.shape != other.numbers.shape or \
           (self.numbers != other.numbers).all():
            raise ValueError("The other molecule does not have the same numbers as this molecule.")
        return fit_rmsd(self.coordinates, other.coordinates)

    def compute_rotsym(self, threshold=1e-3*angstrom):
        """Compute the rotational symmetry number

           Optional argument:
            | ``threshold``  --  only when a rotation results in an rmsd below the given
                                 threshold, the rotation is considered to transform the
                                 molecule onto itself.
        """
        # Generate a graph with a more permissive threshold for bond lengths:
        # (is convenient in case of transition state geometries)
        graph = MolecularGraph.from_geometry(self, scaling=1.5)
        try:
            return compute_rotsym(self, graph, threshold)
        except ValueError:
            raise ValueError("The rotational symmetry number can only be computed when the graph is fully connected.")
