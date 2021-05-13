# xdl

A set of Python scripts for computing and enumerating rigorous abductive (AXp)
and contrastive (CXp) explanations for decision list (DL) models. The
implementation targets DL models printed in the format produced by
[minds](https://github.com/alexeyignatiev/minds).

## Getting Started

Before using `xdl`, make sure you have the following Python packages
installed:

* [pandas](https://pandas.pydata.org/)
* [PySAT](https://github.com/pysathq/pysat)

Please, follow the installation instructions on these projects' websites to
install them properly. (If you spot any other package dependency not listed
here, please, let us know.)

## Usage

`xdl` has a number of parameters, which can be set from the command line. To
see the list of options, run:

```
$ xdl.py -h
```

The implementation supports computing one but also enumerating a given number
(or all) abductive or contrastive explanations either for a given instance, or
all instance of a dataset provided as an input parameter, see the list of
command-line options above. A few example files are presented in the tests
directory.

## Example

```
$ xdl.py -x abd -u -d -n all -D tests/hike2a.csv -m tests/hike2a.cn2 -vv 'Lecture=Yes,Concert=No,ArtExpo=Yes,SeasonSales=No'
MODEL:
IF Lecture != No THEN Hike == No
IF Concert == No THEN Hike == Yes
IF Lecture == No THEN Hike == No
IF TRUE THEN Hike == No

ENCODINDS:
# of classes: 2
min # of vars: 2
avg # of vars: 2.00
max # of vars: 2
min # of clauses: 1
avg # of clauses: 2.00
max # of clauses: 3

EXPLANATIONS:
  inst: "IF Lecture == Yes AND Concert == No AND ArtExpo == Yes AND SeasonSales == No THEN Hike == No"
  expl: "IF Lecture == Yes THEN Hike == No"
  # hypos left: 1
  time: 0.00
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.
