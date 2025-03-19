# VGR - Vault Generic Reporting
Working/transfer area for "Vault Generic Reporting"

## Getting started

But first, this important note: **Nothing is yet really hooked up to Vault, so if you expect output... yeah, no.**

There are four ways to run VGR:

### Statements on the command line

  ```
  $./vgr.py -e 'Print "Hello World"'
  Hello World
  ```

  Multiple statements can be specified using semicolons:

```
$./vgr.py -e 'Set h to "Hello"; Set w to "World"; Print h, w'
Hello World
```

### Statements stored in a file

```
$echo 'Print "Hello World"'>hello.txt
$./vgr.py -f hello.txt
Hello World
```

Multiple files can be run, with the internal variables and environment shared between them:

```
$echo 'Set h to "Hello"; Set w to "World"' > set_vars.txt
$echo 'Print h, w' > hello.txt
$./vgr.py -f set_vars.txt -f hello.txt
Hello World
```

### Statements from stdin

```
$cat set_vars.txt hello.txt | ./vgr.py
Hello World
```

### Using 'Here' documents

```
$../vgr.py <<EOF || echo "FAILED"
Set h to "Hello"
Set w to "World"
Print h, w
EOF
```

### Interactively

```
Type 'exit' to exit
vgr> Set h to "Hello"
vgr> Set w to "World"
vgr> Print h, w
Hello World
vgr>
```

The interactive command line supports history, using `Ctrl-R and` the up and down arrows, as well as some basic file commands and a help system. Just type `help` to get more details. (_NB: help is a work in progress_)

## Variables, Expressions, and Operators

VGR has a hierarchical, global data model, viewed as variables. Some variables are created and _owned_ by the program, but much of the space belongs to you for use in procedures. These parts of the data model are pre-created, and mostly immutable.

* `arg` : user arguments from the command line and some internal variables like `arg.debug`, `arg.echo`, `arg.verbose`, and a few borrowed from AWK (`arg.ofs` and `arg.ors`). These are all read-write, but you can't modify `arg` itself : `Set arg = "foo"` will fail
* `env` : an imported view of the environment. These are strictly read-only.
* `math` : Python math constants such as `math.e` and `math.inf`. Read-only.
* `os` : Operating system constants such as `os.linesep` and `os.extsep`. Read-only.
* `string` : More constants that can be used with string functions, like `string.hexdigits` and `string.ascii_letters`. Read-only.
* `_vgr` : Read-only internals, some dynamic, other changed by shell commands. If your interested, you can always do `Print _vgr.grammar`

Another set of variable are used by VGR `Select` statements and are used by their target data. For example, querying for Key-Value stores will cause ns, mount, and kv variable set with information from Vault. These are not read-only, but values you set will be overwritten by `Select`.

Variables are case sensitive.
```
vgr> set Five to 5
vgr> set five to 6
vgr> print Five, five, FIVE
5 6 None
```
Variable names are hierachical.
```
vgr> set data.Five to 5
vgr> set data.Six to 6
vgr> print data
{'Five': 5, 'Six': 6}
```
Note that you didn't need to create `data` first, and the same goes for deeper hierarchies.
```
vgr> set this.is.several.layers.deep = 5
vgr> print this
{'is': {'several': {'layers': {'deep': 5}}}}
```
Print displays these variable paths as a Python dictionary, which is mostly interchangable with a JSON object. Mostly.

Steps in a variable path can be expressed in _snake_ or _kabab_ case.
```
vgr> set _this.is-several.layers_._deep_ = 5
vgr> print _this.is-several.layers_._deep_
5
```

Steps in the variable path can contain ASCII alphanumeric characters, and the dash or underscore characters. They can start with an underscore, but not a dash:
```
vgr> Set _valid = 0
vgr> Set -not-valid = 0
Set -not-valid = 0
    ^
Unexpected input at line 1, column 5.
Expected NAME.
```

## Things like variables, but they aren't

Besides obvious things like keywords in the language, there are some names that look like variables but aren't. These are `None`, `Null`, `Inf`, `Nan`, `True`, and `False`. These are used in expressions, but can't be used in variables.
```
vgr> set True to False
Error :  Invalid path: True contains reserved values
vgr> Set my.inf = -1
Error :  Invalid path: my.inf contains reserved values
vgr> Set my._inf = -1
```

### Examining Variables

As shown earlier, the most common way looking at the contents of variables is `Print`, but there are others.

#### Print Statement
`Print` works much like AWK's print command. You can print any number of variables or expressions separated by commas.
```
vgr> Set h to "Hello"
vgr> Set w to "World"
vgr> Print h, w
Hello World
  ```
  Invoking `Print` without argument will just create a blank line... but not always.
  `Print` works like AWK, which means that items separated by commas get a _output field separator_ (OFS) placed between them and and an _output record separator_ (ORS) at the end. In VGR, these values are stored in `arg.ofs` and `arg.ors`. They are initially set from the environment, just like with AWK, but you can change them on the command line:
  ```
  vgr.py 'ofs= | ' -e 'Set a to 5; Set b to 6; Print a, b'
5 | 6
  ```
  Or you can change them at runtime:
  ```
vgr> Set arg.ofs = " | "
vgr> Set arg.ors = " |\n"
vgr> Print "Hello", "World"
Hello | World |
  ```
You need to add the `\n` to get a newline in your record separator if you don't want the text to bunch up.

If you set either separators to an empty string or to `None` the default values of a space and a newline will be used.

### Printf Statement
`Printf` uses [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings) to format data. The first argument is the format string, which may require additional expression depending upon its contents.
```
vgr> Set h to "Hello"
vgr> Set w to "World"
vgr> Printf "{} {}!\n", h, w
Hello World!
vgr> Printf "{1}, {0}?\n", w, h
Hello, World?
```
`Printf` does not use the field or record separators, and if you want a newline printed at the end, it must be provided either in the format string or as part of the arguments.

### Exhibit Statement
`Exhibit` is inspired by COBOL, and display information about variables. When looking at a single value, there is little difference from using `Print`:
```
vgr> Print h
Hello
vgr> Exhibit h
h = 'Hello'
```
You can see a bigger difference when printing variables that are dictionaries:
```
vgr> Print arg
{'debug': False, 'echo': False, 'verbose': False, 'ofs': ' ', 'ors': '\n'}
vgr> Exhibit arg
arg.debug = False
arg.echo = False
arg.ofs = ' '
arg.ors = '\n'
arg.verbose = False
```
The purpose of `Exhibit` is to aid in debugging.
