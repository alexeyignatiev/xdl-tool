#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## grepstat.py
##
##  Created on: Sep 04, 2012
##      Author: Alexey S. Ignatiev
##      E-mail: aign@sat.inesc-id.pt
##

#
#==============================================================================
from __future__ import print_function
import getopt
import glob
import gzip
import json
import os
import re
import sys

#
#==============================================================================
stdexpr = {'int': '\\b[0-9]+\\b', 'float': '\\b[0-9]+(.[0-9]+)?\\b'}
stdexpr_rev = {'\\b[0-9]+\\b': 'int', '\\b[0-9]+(.[0-9]+)?\\b': 'float'}


#
#==============================================================================
def process_preamble(logs, benchmark, abbrev):
    """
        Reads description file and creates the preamble.
    """

    with open(os.path.join(logs, 'descr.json'), 'r') as fp:
        preamble = json.load(fp)

    if len(benchmark):
        preamble['benchmark'] = benchmark

    if len(abbrev):
        preamble['abbrev'] = abbrev

    return preamble


#
#==============================================================================
def parse_main_info(fname, ignore_status):
    """
        Parses main information in runsolver's log file.
    """

    status = False
    signal_sent = False
    t = 0.0
    m = 0

    if os.path.exists(fname):
        fp = open(fname, 'r')
    elif os.path.exists(fname + '.gz'):
        fp = gzip.open(fname + '.gz', 'rt')
    else:
        assert 0, 'no file found: {0}'.format(fname)

    for l in fp:
        match = re.match('CPU time', l)
        if match:
            t = float(match.string.split(':')[1].strip())

        match = re.match('Max. virtual', l)
        if match:
            m = float(match.string.split(':')[1].strip())
            if int(m) == m:
                m = int(m)

        if re.match('Sending SIG', l):
            signal_sent = True

        match = re.match('Child status:', l)
        if match and (ignore_status or int(match.string[13:].strip()) == 0):
            status = True

    if status is True and signal_sent is False:
        status = True
    else:
        status = False

    fp.close()
    return status, t, m


#
#==============================================================================
def parse_other_info(fname, exprs, fails, status):
    """
        Parses information in program's log file.
    """

    def typeof(expr):
        if expr in stdexpr_rev:
            return stdexpr_rev[expr]
        else:
            return 'str'

    def append_new_value(info, key, val):
        if key in info:
            if type(info[key]) is not list:
                info[key] = [info[key]]
            info[key].append(val)
        else:
            info[key] = val

    info = {}

    if os.path.exists(fname):
        fp = open(fname, 'r')
    elif os.path.exists(fname + '.gz'):
        fp = gzip.open(fname + '.gz', 'rt')
    else:
        assert 0, 'no file found: {0}'.format(fname)

    for l in fp:
        for expr in exprs:
            m = re.search(expr[1], l)

            if m:
                m = re.search(expr[2], m.string)
                if m:
                    t = typeof(expr[2])
                    v = m.group().strip()
                    if t == 'int':
                        append_new_value(info, expr[0], int(v))
                    elif t == 'float':
                        append_new_value(info, expr[0], float(v))
                    else:
                        append_new_value(info, expr[0], v)

        if status is True:
            for fsign in fails:
                m = re.search(fsign, l)

                if m:
                    status = False
                    break  # it is enough to find one failure

    fp.close()
    return status, info


#
#==============================================================================
def check_size(info_found, num_expected):
    """
        Checks the equality of two numbers: objects expected and objects found.
    """

    if type(info_found) is not list:
        return num_expected == 1
    else:
        return num_expected == len(info_found)


#
#==============================================================================
def process_logs(logs, exprs, fails, check_sz, strip, ignore_status):
    """
        Finds time (if needed) and other expressions
        in all the files of logs directory.
    """

    def find_index(key):
        for i, e in enumerate(exprs):
            if key in e:
                return i

    insts = []
    stats = dict()

    for path, dirs, files in os.walk(logs):
        insts += [f[:-4] for f in glob.glob('{0}/{1}'.format(path, '*.out'))]
        # insts += [f[:-2] for f in glob.glob('{0}/{1}'.format(path, '*.w'))]
        # insts += [f[:-5] for f in glob.glob('{0}/{1}'.format(path, '*.w.gz'))]
    insts.sort()

    for inst in insts:
        # status, t, m = parse_main_info(inst + '.w', ignore_status)
        status, t, m = True, 0, 0

        if ignore_status == 'full':
            status = True

        info = {}
        if exprs or fails:
            status, info = parse_other_info(inst + '.out', exprs, fails, status)

        if status is True and check_sz is True:
            if len(info) < len(exprs):
                # did not find all the expressions
                status = False
            else:
                for (k, v, i) in zip(info.keys(), info.values(), xrange(len(info))):
                    if check_size(v, exprs[i][3]) is False:
                        status = False
                        break

        # deal with multiple objects found for each key
        for (k, v) in zip(info.keys(), info.values()):
            i = find_index(k)
            if type(v) == list and exprs[i][4] != 'all':
                if exprs[i][4] == 'last':
                    info[k] = v[-1]
                elif exprs[i][4] == 'first':
                    info[k] = v[0]
                elif exprs[i][4] == 'max':
                    info[k] = max(v)
                elif exprs[i][4] == 'min':
                    info[k] = min(v)
                elif exprs[i][4] == 'avg':
                    info[k] = sum(v) / float(len(v))
                elif exprs[i][4] in ('count', 'len', 'num'):
                    info[k] = len(v)
            elif exprs[i][4] in ('count', 'len', 'num'):
                info[k] = 1

        i = inst
        if strip:
            if strip == 'basename':
                i = os.path.basename(inst)
            else:
                stripped = 0
                for j, c in enumerate(inst):
                    if c == '/':
                        stripped += 1
                        if stripped == int(strip):
                            j += 1
                            break
                i = inst[j:]

        if status:
            status = (os.stat(inst + '.err').st_size == 0)

        stats[i] = {'status': status, 'rtime': t, 'mempeak': str(m) + ' KiB'}
        stats[i].update(info)

    return stats


#
#==============================================================================
def parse_options():
    """
        Parses command-line options:
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'a:b:cf:hk:l:m:n:o:p:',
                                   ['abbrev=',
                                    'bench=',
                                    'check-sz',
                                    'fail-sign=',
                                    'ignore-status',
                                    'help',
                                    'key=',
                                    'lexpr=',
                                    'multi-obj='
                                    'obj-num=',
                                    'oexpr=',
                                    'strip='])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize())
        usage()
        sys.exit(1)

    kexprs = []
    lexprs = []
    obnums = []
    oexprs = []
    fails = []
    multi_obj = []
    benchmark = ''
    abbrev = ''
    check_sz = False
    strip = 0
    ignore_status = 'value'

    for opt, arg in opts:
        if opt in ('-a', '--abbrev'):
            abbrev = str(arg)
        elif opt in ('-b', '--bench'):
            benchmark = str(arg)
        elif opt in ('-c', '--check-sz'):
            check_sz = True
        elif opt in ('-f', '--fail-sign'):
            fails.append(str(arg))
        elif opt == '--ignore-status':
            ignore_status = str(arg)
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-k', '--key'):
            kexprs.append(str(arg))
            multi_obj.append('last')
        elif opt in ('-l', '--lexpr'):
            lexprs.append(str(arg))
        elif opt in ('-n', '--obj-num'):
            obnums.append(int(arg))
        elif opt in ('-m', '--multi-obj'):
            multi_obj[-1] = str(arg)
        elif str(opt) in ('-o', '--oexpr'):
            if str(arg) in stdexpr:
                oexprs.append(stdexpr[str(arg)])
            else:
                oexprs.append(str(arg))
        elif opt in ('-p', '--strip'):
            strip = str(arg)
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    assert len(kexprs) == len(lexprs) == len(oexprs), 'Number of -k, -l, and -o options should be the same'
    if len(obnums) != len(kexprs):
        obnums = [1 for e in kexprs]

    exprs = list(zip(kexprs, lexprs, oexprs, obnums, multi_obj))
    return exprs, fails, args, benchmark, abbrev, check_sz, strip, ignore_status


#
#==============================================================================
def usage():
    """
        Prints usage message.
    """

    print('Usage: ' + os.path.basename(sys.argv[0]) + ' [options] log-dir')
    print('Options:')
    print('        -a, --abbrev=<string>       Abbreviation to use for this stats set')
    print('        -b, --bench=<string>        Benchmark name to replace the default one')
    print('        -c, --check-sz              Check number of found expressions')
    print('        -f, --fail-sign=<regexp>    Expression to indicate a failure')
    print('        --ignore-status=<string>    Assume status for each instance to be true')
    print('                                    Available values: full, none, value (default = value)')
    print('        -h, --help                  Show this message')
    print('        -k, --key=<regexp>          Key to use')
    print('        -l, --lexpr=<regexp>        Expression to find line')
    print('        -m, --multi-obj=<string>    What object to choose if many')
    print('                                    Available values: all, avg, count, first, last, max, min (default = last)')
    print('        -n, --obj-num=<int>         Expected number of objects to find')
    print('        -o, --oexpr=<regexp>        Expression to find object')
    print('                                    Predefined values: int, float')
    print('        -p, --strip=<int>           Strip the smallest prefix of this size')
    print('                                    Predefined values: basename')


#
#==============================================================================
if __name__ == '__main__':
    exprs, fails, logs, benchmark, abbrev, check_sz, strip, ignore_status = parse_options()

    if len(logs) == 0:
        logs = sys.stdin.readlines()

    for log in logs:
        preamble = process_preamble(log, benchmark, abbrev)
        stats = process_logs(log, exprs, fails, check_sz, strip, ignore_status)
        json.dump({'preamble': preamble, 'stats': stats}, sys.stdout, indent=4, separators=(',', ': '))
        print('', file=sys.stdout)
