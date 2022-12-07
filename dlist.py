#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## dlist.py
##
##  Created on: Feb 2, 2021
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##

# imported modules
#==============================================================================
import collections


#
#==============================================================================
class FeatureValue(object):
    """
        A feature-value pair.
    """

    __instances = {}

    def __new__(cls, feature=None, value=None):
        """
            Constructor to make sure that a unique feature value
            is created for a unit pair of arguments.
        """

        key = tuple([feature, value])

        if key not in FeatureValue.__instances:
            FeatureValue.__instances[key] = super(FeatureValue, cls).__new__(cls)

        return FeatureValue.__instances[key]

    def __init__(self, feature, value):
        """
            Initialiser.
        """

        self.feat = feature
        self.val = value

    def __str__(self):
        """
            String representation of a literal.
        """

        return '{0} == {1}'.format(self.feat, self.val)


#
#==============================================================================
class Literal(object):
    """
        Representation of a literal.
    """

    __instances = {}

    def __new__(cls, feature=None, value=None, positive=True):
        """
            Constructor to make sure unique literals are created
            for unique triples of arguments.
        """

        key = tuple([feature, value, positive])

        if key not in Literal.__instances:
            Literal.__instances[key] = super(Literal, cls).__new__(cls)

        return Literal.__instances[key]

    def __init__(self, feature, value, positive=True):
        """
            Initialiser.
        """

        self.feat = feature
        self.val = value
        self.pos = positive

    def __str__(self):
        """
            String representation of a literal.
        """

        return '{0} {1} {2}'.format(self.feat, '==' if self.pos else '!=',
                self.val)


#
#==============================================================================
class Rule(object):
    """
        Representation of a single rule.
    """

    def __init__(self, preamble, label):
        """
            Constructor (default rules are currently unsupported).
        """

        self.fvals = preamble[:]
        self.label = label

        # for accessing rule literals by feature names
        self.by_name = collections.defaultdict(lambda: [])
        for fv in self.fvals:
            self.by_name[fv.feat].append(tuple([fv.val, fv.pos]))

    def __len__(self):
        """
            Magic method for computing length.
        """

        return len(self.fvals)

    def __getitem__(self, key):
        """
            Read-access to a literal.
        """

        return self.fvals[key]

    def __setitem__(self, key, value):
        """
            Write-access to a literal.
        """

        self.fvals[key] = value

    def __iter__(self):
        """
            Iterator over the literals.
        """

        for lit in self.fvals:
            yield lit

    def __str__(self):
        """
            String representation of a rule.
        """

        return 'IF {0} THEN {1}'.format(', '.join([str(fv) for fv in self.fvals]),
                str(self.label))

    def applies_to(self, instance, return_failing=False):
        """
            Check if the rule applies to an instance.
            The instance must be a list of FeatureValue objects.
        """

        # traversing all feature-values of the instance
        for fv in instance:
            # checking if a feature value is in the rule
            if fv.feat in self.by_name:
                for rval in self.by_name[fv.feat]:
                    # checking if the value in the rule is the same but
                    # the literal in the rule is opposite,
                    # or if the value is different in the rule
                    if (rval[0] == fv.val and rval[1] == False) or (rval[0] != fv.val and rval[1] == True):
                        if return_failing:
                            return fv
                        else:
                            return False

        # no failure indicates that the rule applies to this instance
        return True


#
#==============================================================================
class DecisionList(object):
    """
        Decision list representation.
    """

    def __init__(self, from_file=None, from_fp=None, data=None):
        """
            Constructor.
        """

        self.rules = []
        self.default = None

        # for accessing all feature values
        self.fvals = collections.defaultdict(lambda: collections.defaultdict(lambda: [None, None]))

        # this will be used to access the rules by their class
        self.by_class = collections.defaultdict(lambda: [])

        # first, we need to process the data
        assert data, 'No dataset is given'
        self.process_data(data)

        if from_file:
            with open(from_file, 'r') as fp:
                self.parse(fp)
        elif from_fp:
            self.parse(from_fp)
        else:
            assert 0, 'No decision list provided'

    def process_data(self, data):
        """
            Read and process feature values. The idea is to use all possible
            values for each feature so that all the necessary Boolean
            variables are created and properly connected by the encoder.
        """

        for feat, vals in zip(data.names, data.feats):
            for val in vals:
                self.fvals[feat][val][1] = Literal(feature=feat, value=val)

    def parse(self, fp):
        """
            Parse a decision list from a file pointer.
        """

        lines = fp.readlines()
        lines = filter(lambda x: 'cover:' in x, lines)
        lines = map(lambda x: x.split(':', 1)[1].strip(), lines)

        for line in lines:
            body, label = line.split(' => ')

            lname, lval = label.strip('\'').split(': ')
            if self.fvals[lname][lval][1] is None:
                self.fvals[lname][lval][1] = Literal(feature=lname, value=lval)
            label = self.fvals[lname][lval][1]

            if body == 'true':
                assert not self.default, 'A single default rule is allowed'

                self.default = label
                continue

            # traversing the body and creating a proper preamble
            preamble = []
            for l in body.split(', '):

                if l[0] == '\'':
                    name, val = l.strip('\'').rsplit(': ', 1)
                    if self.fvals[name][val][1] is None:
                        self.fvals[name][val][1] = Literal(feature=name,
                                value=val, positive=True)
                    lnew = self.fvals[name][val][1]

                elif l[0] == 'n':  # negative literal
                    name, val = l[4:].strip('\'').rsplit(': ', 1)
                    if self.fvals[name][val][0] is None:
                        self.fvals[name][val][0] = Literal(feature=name,
                                value=val, positive=False)
                    lnew = self.fvals[name][val][0]

                preamble.append(lnew)

            self.by_class[label].append(len(self.rules))
            self.rules.append(Rule(preamble, label))

        # number of rules and literals
        self.nof_rules = len(self.rules) + int(self.default != None)
        self.nof_lits = sum([len(r) for r in self.rules]) + int(self.default != None)

    def __str__(self):
        """
            String representation of a decision list.
        """

        ret = ''
        for rule in self.rules:
            ret += str(rule) + '\n'
        ret += 'IF TRUE THEN {0}'.format(self.default)

        return ret

    def execute(self, instance, input_format=False):
        """
            Make prediction for a given instance.
            The instance must be a list of FeatureValue objects.
        """

        if input_format:
            instance = [FeatureValue(*fv.split('=')) for fv in instance]

        for rule in self.rules:
            # print(rule)
            if rule.applies_to(instance):
                # print('applies')
                return rule.label
            # print('fails')

        # no rule applies => using the default class
        return self.default

    def explain(self, instance):
        """
            Compute a "default" explanation for a given instance. Here,
            instance should be given as a tuple of equality strings. The
            procedure follows the flow of self.execute() but instead of
            checking whether a rule applies, it extracts incompatible
            features.
        """

        inst = [FeatureValue(*fv.split('=')) for fv in instance]
        expl, eset = [], set()

        for rule in self.rules:
            applies = rule.applies_to(inst, return_failing=True)
            if applies == True:
                expl += list(filter(lambda fv: fv.feat in rule.by_name and fv not in eset, inst))
                break
            elif applies not in eset:
                expl += [applies]
                eset.add(applies)

        return tuple(['{0}={1}'.format(fv.feat, fv.val) for fv in expl])
