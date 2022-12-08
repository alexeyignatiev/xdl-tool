#!/usr/bin/env python -u
#-*- coding:utf-8 -*-

import os
import sys

if __name__ == '__main__':
    with open(sys.argv[1], 'r') as fp:
        files = fp.readlines()

    cmd = './xdl.py -R -x abd -u -d -n all -e pw -r lin -vv'

    for model in files:
        model = model.strip()
        stderr = os.path.splitext(model)[0] + '.err'
        stdout = os.path.splitext(model)[0] + '.out'
        dataset = model[:-11] + '.csv.gz'
        dataset = dataset.replace('cn2/', 'orig/')
        print(model)
        os.system('runsolver.py -e {0} -o {1} -t 1800 "{2}"'.format(stderr, stdout, '{0} -m {1} -D {2}'.format(cmd, model, dataset)))
