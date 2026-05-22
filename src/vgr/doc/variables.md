## Variables, Expressions, and Operators

VGR has a hierarchical, global data model, viewed as variables. Some variables are created and _owned_ by the program, but much of the space belongs to you for use in procedures. These parts of the data model are pre-created, and mostly immutable.

* `args` : list of positional user arguments from the command line
* `env` : an imported view of the environment including `env.OFS` and `env.ORS` used by `Print`.
* `math` : Python math constants such as `math.e` and `math.inf`. Read-only.
* `os` : Operating system constants such as `os.linesep` and `os.extsep`. Read-only.
* `string` : More constants that can be used with string functions, like `string.hexdigits` and `string.ascii_letters`. Read-only.
* `vgr` : Read-only internals, some dynamic, other changed by commands.

Variables are case sensitive.

```vgr
Set Five To 5
Set five To 6
Print Five, five, FIVE
5 6 None
```

Variable names are hierachical.

```vgr
Set data.Five To 5
Set data.Six To 6
Print data
{'Five': 5, 'Six': 6}
```

Note that you didn't need to create `data` first, and the same goes for deeper hierarchies.

```vgr
Set this.is.several.layers.deep To 5
Print this
{'is': {'several': {'layers': {'deep': 5}}}}
```

Print displays these variable paths as a Python dictionary, which is mostly interchangable with a JSON object. Mostly.

Steps in a variable path can be expressed in _snake_ or _kabab_ case.

```vgr
Set _this.is-several.layers_._deep_ To 5
Print _this.is-several.layers_._deep_
5
```

Steps in the variable path can contain ASCII alphanumeric characters, and the dash or underscore characters. They can start with an underscore, but not a dash:

```vgr
Set _valid To 0
Set -not-valid To 0
Set -not-valid To 0
    ^
Unexpected input at line 1, column 5.
Expected NAME.
```

### Removing Values

The Unset statment is used to remove variables.

```vgr
Set data.Five To 5
Set data.Six To 6
Print data
{'Five': 5, 'Six': 6}

Unset data.Five
Print data
{'Six': 6}
Unset data.Six
Print data
{}

Unset data
Print data
None
```

If you ask to remove a variable that doesn't exist, or part of its path do not exist, the request is ignored.

## Things like variables, but they aren't

Besides obvious things like keywords in the language, there are some names that look like variables but aren't. These are `None`, `Null`, `Inf`, `Nan`, `True`, and `False`. These are used in expressions, but can't be used in variables.

```vgr
Set True To False
Error : Invalid path: True contains reserved values
Set my.inf To -1
Error : Invalid path: my.inf contains reserved values
Set my._inf To -1
```

### Examining Variables

As shown earlier, the most common way looking at the contents of variables is `Print`, but there are others.

#### Print Statement

`Print` works much like AWK's print command. You can print any number of variables or expressions separated by commas.

```vgr
Set h To "Hello"
Set w To "World"
Print h, w
Hello World
```

Invoking `Print` without argument will just create a blank line... but not always. `Print` works like AWK, which means that items separated by commas get a _output field separator_ (OFS) placed between them and and an _output record separator_ (ORS) at the end. In VGR, as with awk, these values are stored in `env.OFS` and `env.ORS`:

```Bash
export OFS=" | "
vgr --execute 'Set a to 5; Set b to 6; Print a, b'
5 | 6
```

Or you can change them at runtime:

```vgr
Set env.OFS To " | "
Set env.ORS To " |\n"
Print "Hello", "World"
Hello | World |
 ```

You need to add the `\n` to get a newline in your record separator if you don't want the text to bunch up.

If you set either separators to an empty string or to `None` the default values of a space and a newline will be used.

### Printf Statement

`Printf` uses [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings) to format data. The first argument is the format string, which may require additional expression depending upon its contents.

```vgr
Set h To "Hello"
Set w To "World"
Printf "{} {}!\n", h, w
Hello World!

Printf "{1}, {0}?\n", w, h
Hello, World?
```

`Printf` does not use the field or record separators, and if you want a newline printed at the end, it must be provided either in the format string or as part of the arguments.

### Exhibit Statement

`Exhibit` displays information about variables. When looking at a single value, there is little difference from using `Print`:

```vgr
Print h
Hello
Exhibit h
h = 'Hello'
```

You can see a bigger difference when printing variables that are dictionaries:

```vgr
Print math
{'pi': 3.141592653589793, 'e': 2.718281828459045, 'tau': 6.283185307179586, 'inf': inf, 'nan': nan, 'neg_inf': -inf, 'float': {'max': 1.7976931348623157e+308, 'min': 2.2250738585072014e-308}, 'random': 0.8042746395530653, 'random100': 97}

Exhibit math
math.e = 2.718281828459045
math.float.max = 1.7976931348623157e+308
math.float.min = 2.2250738585072014e-308
math.inf = inf
math.nan = nan
math.neg_inf = -inf
math.pi = 3.141592653589793
math.random = 0.9730055215356191
math.random100 = 81
math.tau = 6.283185307179586
```

The purpose of `Exhibit` is to aid in debugging.
