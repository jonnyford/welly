#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines a multi-well 'project'.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import glob
from collections import Counter

import numpy as np

from .well import Well, WellError


class Project(object):
    """
    Just a list of Well objects.

    One day it might want its own CRS, but then we'd have to cast the CRSs of
    the contained data.

    """
    def __init__(self, list_of_Wells):
        self.alias = None
        self.__list = list_of_Wells
        self.__index = 0
        self._iter = iter(self.__list)  # Set up iterable.

    def __repr__(self):
        s = [w.uwi for w in self.__list]
        return "Project({0})".format('\n'.join(s))

    def __str__(self):
        s = [w.uwi for w in self.__list]
        return '\n'.join(s)

    def __getitem__(self, key):
        if type(key) is slice:
            i = key.indices(len(self.__list))
            result = [self.__list[n] for n in range(*i)]
            return Project(result)
        elif type(key) is list:
            result = []
            for j in key:
                result.append(self.__list[j])
            return Project(result)
        else:
            return self.__list[key]

    def __setitem__(self, key, value):
        self.__list[key] = value

    def __iter__(self):
        return self

    def __next__(self):
        try:
            result = self.__list[self.__index]
        except IndexError:
            self.__index = 0
            raise StopIteration
        self.__index += 1
        return result

    def next(self):
        """
        Retains Python 2 compatibility.
        """
        return self.__next__()

    def __len__(self):
        return len(self.__list)

    def __contains__(self, item):
        if isinstance(item, Well):
            for d in self.__list:
                if item == d:
                    return True
        return False

    def __add__(self, other):
        if isinstance(other, self.__class__):
            result = self.__list + other.__list
            return Project(result)
        elif isinstance(other, Well):
            result = self.__list + [other]
            return Project(result)
        else:
            raise WellError("You can only add legends or decors.")

    def _repr_html_(self):
        """
        Jupyter Notebook magic repr function.
        """
        all_curves = []
        for well in self:
            all_curves += list(well.data.keys())
        all_curves = [c for c in all_curves if c not in ["DEPTH", "DEPT"]]
        top = Counter(all_curves).most_common()
        curve_names = [i[0] for i in top]
        # Make header
        html_head = '<tr><th>Well (UWI) </th><th>Data </th>'
        for thing in curve_names:
            html_head += ('<th>' + thing + '</th>')
        html_head += ('</tr>')
        # Make rows
        rows = ''
        for well in self.__list:
            this_row = ''
            ncurves = str(len(well.data))
            curves = [c if c in well.data.keys() else str(0) for c in curve_names]
            this_row += '<td>{}</td><td>{} curves</td>'.format(well.uwi, ncurves)
            for curve in curves:
                if curve in well.data:
                    color = 'grey'
                if curve == str(0):
                    color = 'white'
                    curve = ''
                this_row += ('<td bgcolor=' + color + '>' + curve + '</td>')
            this_row += ('</tr>')
            rows += this_row
        html = '<table>{}{}</table>'.format(html_head, rows)
        return html

        def make_one_row(well, curves):
            this_row = ''
            ncurves = str(len(well.data))
            this_row += '<td>{}</td><td>{} curves</td>'.format(well.uwi, ncurves)
            for curve in curves:
                if curve in well.data:
                    color = 'grey'
                if curve == str(0):
                    color = 'white'
                    curve = ''
                this_row += ('<td bgcolor=' + color + '>' + curve + '</td>')
            this_row += ('</tr>')
            return this_row
        return html

    @classmethod
    def from_las(cls, path, remap=None, funcs=None):
        """
        Constructor. Essentially just wraps ``Well.from_las()``, but is more
        convenient for most purposes.

        Args:
            path (str): The path of the LAS files, e.g. 'data/*.las'. It will
                attempt to load everything it finds, so make sure it only leads
                to LAS files.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        Returns:
            project. The project object.
        """
        list_of_Wells = [Well.from_las(f) for f in glob.iglob(path)]
        return cls(list_of_Wells)

    def data_as_matrix(self, keys, window_length=3):
        """
        Make X.

        Needs to return z probably...

        """
        # Seed with known size.
        X = np.zeros(window_length * len(keys))

        # Build up the data.
        for w in self.__list:
            _X, _ = w.data_as_matrix(keys,
                                     window_length=window_length,
                                     return_basis=True,
                                     alias=self.alias)
            X = np.vstack([X, _X])

        # Get rid of the 'seed'.
        X = X[1:]

        return X
