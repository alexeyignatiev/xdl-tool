#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## enc.py
##
##  Created on: Feb 5, 2021
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##

# imported modules
#==============================================================================
import collections
import copy
from dlist import FeatureValue
from pysat.card import *
from pysat.formula import IDPool, WCNF


#
#==============================================================================
class DLEncoding(object):
    """
        Boolean encoding of explanation extraction for decision lists.
    """

    def __init__(self, dlist, options):
        """
            Constructor.
        """

        self.options = options

        # the list of class labels
        self.labels = list(dlist.by_class.keys())

        # we have multiple encodings, one per class
        self.encs = {}

        # list of vars encoding rules
        self.rvars = []

        # making common variables for feature-value pairs
        self.vars, formula = self.encode_features(dlist.fvals, self.labels,
                dlist.default)

        # encoding all the rules
        self.encode_rules(dlist.rules, formula)

        # finally, encoding each class as a separate formula
        for label, rules in dlist.by_class.items():
            # first copying all the clauses
            self.encs[label] = copy.deepcopy(formula)

            # then encoding the (mis-)classification process
            self.encode(label, rules, default=dlist.default==label)

    def encode_features(self, fvals, labels, default):
        """
            Introduce all the common Boolean variables (input and output).
        """

        labelname = default.feat

        # initialising variable manager and formula
        vpool, formula = IDPool(), WCNF()

        # iterating over features
        for feat, values in fvals.items():
            if feat == labelname:
                continue
            if len(values) <= 2:
                values = sorted(values)
                fval1 = FeatureValue(feat, values[0])
                vid = vpool.id(fval1)  # new variable id
                if len(values) == 2:
                    fval2 = FeatureValue(feat, values[1])

                    # using the opposite value
                    vpool.obj2id[fval2] = -vid
                    vpool.id2obj[-vid] = fval2
            else:
                lits = []
                for val in sorted(values):
                    fval = FeatureValue(feat, val)
                    lits.append(vpool.id(fval))  # creating the variables

                # a feature can take exactly 1 value
                formula.extend(CardEnc.equals(lits=lits, vpool=vpool,
                    encoding=self.options.cenc))

        return vpool, formula

    def encode_rules(self, rules, formula):
        """
            Encoding all rules.
        """

        self.rvars = []
        for rule in rules:
            self.encode_rule(rule, formula)

        assert len(self.rvars) == len(rules)

    def encode_rule(self, rule, formula):
        """
            Encode rule.
        """

        if len(rule) > 1:
            rvar = self.vars.id(str(rule))  # creating a new variable

            lvars = []
            for lit in rule:
                lvar = self.vars.id(FeatureValue(lit.feat, lit.val)) * (1 if lit.pos else -1)
                lvars.append(-lvar)
                formula.append([-rvar, lvar])
            formula.append(lvars + [rvar])
        else:
            assert FeatureValue(rule[0].feat, rule[0].val) in self.vars.obj2id, \
                    'No variable for feature-value {0}'.format(FeatureValue(rule[0].feat, rule[0].val))

            # no need for new variable
            # we reuse the variable for the only literal the rule has
            rvar = self.vars.id(FeatureValue(rule[0].feat, rule[0].val)) * (1 if rule[0].pos else -1)
            self.vars.obj2id[str(rule)] = rvar

        self.rvars.append(rvar)

    def encode_nofire(self, index):
        """
            Return a clause enforcing that a given rule does not fire a
            prediction. Concretely, enforce that either one of the preceding
            rules fires or the current one does fire.
        """

        cl = [self.rvars[i] for i in range(index)] + [-self.rvars[index]]

        # the clause may contain duplicate literals
        return sorted(set(cl))

    def encode(self, label, rules, default=False):
        """
            Encode one class and update the corresponding CNF formula.
        """

        # for every rule, adding a constraint enforcing it *not to fire*
        for rule in rules:
            self.encs[label].append(self.encode_nofire(rule))

        if default:
            # default rule belongs to this class, i.e. we need to
            # enforce that any rule fires before the default one
            self.encs[label].append(sorted(set(self.rvars)))
