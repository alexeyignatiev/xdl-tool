#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## data.py
##
##  Created on: Sep 20, 2017
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##

#
#==============================================================================
from __future__ import print_function
import collections
import gzip
import pandas
import six
from six.moves import range


#
#==============================================================================
class Data(object):
    """
        Class for representing data (training instances).
    """

    def __init__(self, filename=None, fpointer=None, dataframe=None,
            names=None, separator=','):
        """
            Constructor and parser.
        """

        self.names = None
        self.nm2id = None
        self.samps = None
        self.wghts = None
        self.feats = None

        if filename:
            if filename.endswith('.gz'):
                with gzip.open(filename, 'rt') as fp:
                    self.parse_fp(fp, separator)
            else:
                with open(filename, 'r') as fp:
                    self.parse_fp(fp, separator)
        elif fpointer:
            self.parse_fp(fpointer, separator)
        elif dataframe is not None:
            self.parse_dframe(dataframe, names=names)

    def parse_fp(self, fp, separator):
        """
            Parse input CSV file.
        """

        # reading data set from file
        lines = fp.readlines()

        # dropping class labels
        lines = [','.join(line.strip().split(separator)[:-1]) for line in lines]

        # reading preamble
        self.names = [w.strip() for w in lines[0].strip().split(',')]
        self.feats = [set([]) for n in self.names]
        del(lines[0])

        # filling name to id mapping
        self.nm2id = {name: i for i, name in enumerate(self.names)}

        # reading training samples
        self.samps, self.wghts = [], []

        for line, w in six.iteritems(collections.Counter(lines)):
            sample = [word.strip() for word in line.strip().split(',')]
            for i, f in enumerate(sample):
                if f:
                    self.feats[i].add(f)
            self.samps.append(sample)
            self.wghts.append(w)

        # translating sets of values into tuples
        # (they aren't going to be updated anymore)
        self.feats = [tuple(sorted(feats)) for feats in self.feats]

    def __iter__(self):
        """
            Iterator over all instances of the dataset.
        """

        for samp in self.samps:
            yield tuple(map(lambda f: '{0}={1}'.format(f[0], f[1]),
                zip(self.names, samp)))
