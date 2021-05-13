#!/usr/bin/env python3
#-*- coding:utf-8 -*-
##
## cn2.py (should be used only with Python 3)
##
##  Created on: Feb 20, 2018
##      Author: Filipe Pereira, Alexey S. Ignatiev
##      E-mail: filipe.pereira.1995@gmail.com, aignatiev@ciencias.ulisboa.pt
##

#
#==============================================================================
from __future__ import print_function
import getopt
import gzip
from io import StringIO
import Orange
import os
from six.moves import range
import sys
import tempfile


#
#==============================================================================
def dump_result(data, clf, learner, to=sys.stdout):
    """
        Print resulting (unordered) list of rules to a file pointer.
    """

    nof_lits = 1  # count the default branch as well
    for rule in clf.rule_list:
        nof_lits += rule.length

        if orange_fmt:
            print('c* cover:', str(rule), file=to)
        else:
            # printing in the MinDS format
            premise, label = str(rule).split(' THEN ')

            # processing premise
            premise = premise[3:].split(' AND ')
            for i in range(len(premise)):
                if '!=' in premise[i]:
                    premise[i] = 'not \'{0}\''.format(premise[i].replace('!=', ': '))
                else:  # '==' is expected
                    premise[i] = '\'{0}\''.format(premise[i].replace('==', ': '))

            premise = ', '.join(premise)
            if premise == '\'TRUE\'':
                premise = 'true'

            # processing label
            label = label.replace('=', ': ')

            print('c* cover:', premise, '=>', label, file=to)

    print('c* cover size:', len(clf.rule_list), file=to)
    print('c* cover wght:', nof_lits, file=to)

    # testing accuracy using Orange
    res = Orange.evaluation.TestOnTrainingData(data, [learner])
    acc = Orange.evaluation.scoring.CA(res)

    print('c* accur: {0:.2f}%'.format(100 * float(acc[0])), file=to)


#
#==============================================================================
def parse_options():
    """
        Parses command-line options.
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'hlos:',
                                   ['help',
                                    'list',
                                    'orange-fmt',
                                    'sd',
                                    'sep='])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize() + '\n')
        usage()
        sys.exit(1)

    dlist = False
    orange_fmt = False
    sdlearner = False
    sep = ','

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-l', '--list'):
            dlist = True
        elif opt in ('-o', '--orange-fmt'):
            orange_fmt = True
        elif opt in ('-s', '--sep'):
            sep = str(arg)
        elif opt == '--sd':
            sdlearner = True
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return dlist, orange_fmt, sep, sdlearner, args


#
#==============================================================================
def usage():
    """
        Prints help message.
    """

    print('Usage:', os.path.basename(sys.argv[0]), '[options] file')
    print('Options:')
    print('        -h, --help')
    print('        -l, --list            Compute a decision list (instead of a set)')
    print('        -o, --orange-fmt      Print in the Orange format')
    print('        -s, --sep=<string>    Separator used in the input CSV file (default = \',\')')
    print('        --sd                  Use SD learner.')


#
#==============================================================================
if __name__ == '__main__':
    dlist, orange_fmt, sep, sdlearner, files = parse_options()

    if files:
        if files[0].endswith('.gz'):
            with gzip.open(files[0], 'rt') as fp:
                dset = fp.readlines()
        else:
            with open(files[0]) as fp:
                dset = fp.readlines()

        # processing data attributes
        dset[0] = ['D#{0}'.format(name) for name in dset[0].split(sep)]
        dset[0][-1] = 'c' + dset[0][-1]
        dset[0] = '{0}'.format(sep).join(dset[0])

        # reading the dataset by Orange
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv') as fp:
            # first, saving the file (Orange does not support reading from strings)
            fp.writelines(dset)
            fp.seek(0)

            data = Orange.data.Table.from_file(fp.name)

        # creating a CN2 learner
        if dlist:
            if sdlearner:
                learner = Orange.classification.CN2SDLearner()
            else:
                learner = Orange.classification.CN2Learner()
        else:
            if sdlearner:
                learner = Orange.classification.CN2SDUnorderedLearner()
            else:
                learner = Orange.classification.CN2UnorderedLearner()

        # classifier
        clf = learner(data)

        # print the result to stdout
        dump_result(data, clf, learner)
