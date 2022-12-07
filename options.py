#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## options.py
##
##  Created on: Feb 7, 2021
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##

#
#==============================================================================
from __future__ import print_function
import getopt
import os
from pysat.card import EncType
import sys

#
#==============================================================================
encmap = {
    'pw': EncType.pairwise,
    'seqc': EncType.seqcounter,
    'cardn': EncType.cardnetwrk,
    'sortn': EncType.sortnetwrk,
    'tot': EncType.totalizer,
    'mtot': EncType.mtotalizer,
    'kmtot': EncType.kmtotalizer
}


#
#==============================================================================
class Options(object):
    """
        Class for representing command-line options.
    """

    def __init__(self, command):
        """
            Constructor.
        """

        self.cenc = 'pw'
        self.dataset = None
        self.inst = None
        self.model = None
        self.reduce = 'none'
        self.redcheck = False
        self.smallest = False
        self.solver = 'g3'
        self.unit_mcs = False
        self.use_cld = False
        self.use_mhs = False
        self.verb = 0
        self.xnum = 1
        self.xtype = 'abd'

        if command:
            self.parse(command)

    def parse(self, command):
        """
            Parser.
        """

        self.command = command

        try:
            opts, args = getopt.getopt(command[1:], 'dD:e:hHm:Mn:r:Rs:uvx:',
                    ['dataset=', 'enc=', 'help', 'model', 'reduce=', 'redcheck',
                        'smallest', 'solver=', 'trim=', 'verbose', 'unit-mcs',
                        'use-cld', 'use-mhs', 'xnum=', 'xtype='])
        except getopt.GetoptError as err:
            sys.stderr.write(str(err).capitalize())
            self.usage()
            sys.exit(1)

        for opt, arg in opts:
            if opt in ('-d', '--use-cld'):
                self.use_cld = True
            elif opt in ('-D', '--dataset'):
                self.dataset = str(arg)
            elif opt in ('-e', '--enc'):
                self.cenc = str(arg)
            elif opt in ('-h', '--help'):
                self.usage()
                sys.exit(0)
            elif opt in ('-H', '--use-mhs'):
                self.use_mhs = True
            elif opt in ('-m', '--model'):
                self.model = str(arg)
            elif opt in ('-M', '--minimum'):
                self.smallest = True
            elif opt in ('-n', '--xnum'):
                self.xnum = str(arg)
                self.xnum = -1 if self.xnum == 'all' else int(self.xnum)
            elif opt in ('-r', '--reduce'):
                self.reduce = str(arg)
            elif opt in ('-R', '--redcheck'):
                self.redcheck = True
            elif opt in ('-s', '--solver'):
                self.solver = str(arg)
            elif opt in ('-u', '--unit-mcs'):
                self.unit_mcs = True
            elif opt in ('-v', '--verbose'):
                self.verb += 1
            elif opt in ('-x', '--xtype'):
                self.xtype = str(arg)
            else:
                assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

        # we expect a dataset to be given
        assert self.dataset, 'Wrong or no dataset is given'
        if args:
            self.inst = tuple(args[0].split(','))

        self.cenc = encmap[self.cenc]

    def usage(self):
        """
            Prints usage message.
        """

        print('Usage: ' + os.path.basename(self.command[0]) + ' [options] [instance]')
        print('Options:')
        print('        -d, --use-cld             Use CLD heuristic')
        print('        -D, --dataset=<string>    Path to dataset file (default: <none>)')
        print('        -e, --enc=<string>        Cardinality encoding to use')
        print('                                  Available values: cardn, kmtot, mtot, sortn, tot (default = pw)')
        print('        -h, --help                Show this message')
        print('        -H, --use-mhs             Use hitting set based enumeration')
        print('        -m, --model=<string>      Path to model file (default: <stdin>)')
        print('        -M, --minimum             Compute a smallest size explanation (instead of a subset-minimal one)')
        print('        -n, --xnum=<int>          Number of explanations to compute')
        print('                                  Available values: [1, INT_MAX], all (default = 1)')
        print('        -r, --reduce=<string>     Extract an MUS from each unsatisfiable core')
        print('                                  Available values: lin, none, qxp (default = none)')
        print('        -R, --red-check           Apply an explanation redundancy check for a default explanation')
        print('        -s, --solver=<string>     SAT solver to use')
        print('                                  Available values: g3, g4, lgl, mcb, mcm, mpl, m22, mc, mgh (default = g3)')
        print('        -u, --unit-mcs            Detect and block unit-size MCSes')
        print('        -v, --verbose             Be verbose')
        print('        -x, --xtype=<string>      Type of explanation to compute: abductive or contrastive')
        print('                                  Available values: abd, con (default = abd)')
