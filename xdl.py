#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## xdl.py
##
##  Created on: Feb 2, 2021
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##

#
#==============================================================================
from data import Data
from dlist import DecisionList
from enc import DLEncoding
from exp import DLExplainer
from options import Options
import statistics
import sys


#
#==============================================================================
if __name__ == '__main__':
    options = Options(sys.argv)

    # first, reading a dataset
    if options.dataset:
        data = Data(filename=options.dataset, separator=',')

    # then reading a DL model
    if options.model:
        model = DecisionList(from_file=options.model, data=data)
    else:
        model = DecisionList(from_fp=sys.stdin, data=data)

    if options.verb > 1:
        print('MODEL:')
        print(model)
        print('\nENCODINDS:')

    # creating the encodings
    encoder = DLEncoding(model, options)

    if options.verb:
        print('# of classes:', len(encoder.encs))
        print('min # of vars:', min([enc.nv for enc in encoder.encs.values()]))
        print('avg # of vars: {0:.2f}'.format(statistics.mean([enc.nv for enc in encoder.encs.values()])))
        print('max # of vars:', max([enc.nv for enc in encoder.encs.values()]))
        print('min # of clauses:', min([len(enc.hard) for enc in encoder.encs.values()]))
        print('avg # of clauses: {0:.2f}'.format(statistics.mean([len(enc.hard) for enc in encoder.encs.values()])))
        print('max # of clauses:', max([len(enc.hard) for enc in encoder.encs.values()]))
        print('\nEXPLANATIONS:')

    # creating the explainer object
    explainer = DLExplainer(model, encoder, options)

    if options.inst:
        if options.redcheck:
            # getting default explanation
            explainer.redcheck = model.explain(options.inst)

        explainer.explain(options.inst, smallest=options.smallest,
                xtype=options.xtype, xnum=options.xnum, unit_mcs=options.unit_mcs,
                use_cld=options.use_cld, use_mhs=options.use_mhs,
                reduce_=options.reduce)
    else:
        # no instance is provided, hence
        # explaining all instances of the dataset
        # here are some stats
        nofex, minex, maxex, avgex, times, dxprd = [], [], [], [], [], []
        for inst in data:
            if options.redcheck:
                # getting default explanation
                explainer.redcheck = model.explain(inst)

            expls = explainer.explain(inst, smallest=options.smallest,
                    xtype=options.xtype, xnum=options.xnum,
                    unit_mcs=options.unit_mcs, use_cld=options.use_cld,
                    use_mhs=options.use_mhs, reduce_=options.reduce)

            if options.redcheck:
                dxprd.append((len(explainer.redcheck) - len(expls[0])) / len(explainer.redcheck))

            nofex.append(len(expls))
            minex.append(min([len(e) for e in expls]))
            maxex.append(max([len(e) for e in expls]))
            avgex.append(statistics.mean([len(e) for e in expls]))
            times.append(explainer.time)

        if options.verb:
            print('# of insts:', len(nofex))
            print('tot # of expls:', sum(nofex))
            print('min # of expls:', min(nofex))
            print('avg # of expls: {0:.2f}'.format(statistics.mean(nofex)))
            print('max # of expls:', max(nofex))
            print('')
            print('Min expl sz:', min(minex))
            print('min expl sz: {0:.2f}'.format(statistics.mean(minex)))
            print('avg expl sz: {0:.2f}'.format(statistics.mean(avgex)))
            print('max expl sz: {0:.2f}'.format(statistics.mean(maxex)))
            print('Max expl sz:', max(maxex))
            print('')
            print('tot time: {0:.2f}'.format(sum(times)))
            print('min time: {0:.2f}'.format(min(times)))
            print('avg time: {0:.2f}'.format(statistics.mean(times)))
            print('max time: {0:.2f}'.format(max(times)))

            if options.redcheck:
                print('')
                print('min dxrd: {0:.2f}'.format(min(dxprd)))
                print('avg dxrd: {0:.2f}'.format(statistics.mean(dxprd)))
                print('max dxrd: {0:.2f}'.format(max(dxprd)))
