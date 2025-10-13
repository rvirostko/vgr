# VGR - Vault Generic Reporting

Working/transfer area for "Vault Generic Reporting"

## DEPRECATED : this text is being integrated into the REPL help command

## Getting started

There are four ways to run VGR:

### Statements on the command line

```Bash
$./vgr.py -e 'Print "Hello World"'
Hello World
```

  Multiple statements can be specified using semicolons:

```Bash
$./vgr.py -e 'Set h to "Hello"; Set w to "World"; Print h, w'
Hello World
```

Note that semi-colons betweens statements of any type are optional, but it adds clarity when you have more than one statement per line.

### Statements stored in a file

```Bash
$echo 'Print "Hello World"'>hello.txt
$./vgr.py -f hello.txt
Hello World
```

Multiple files can be run, with the internal variables and environment shared between them:

```Bash
$echo 'Set h to "Hello"; Set w to "World"' > set_vars.txt
$echo 'Print h, w' > hello.txt
$./vgr.py -f set_vars.txt -f hello.txt
Hello World
```

### Statements from stdin

```Bash
$cat set_vars.txt hello.txt | ./vgr.py
Hello World
```

### Using 'Here' documents

```Bash
$../vgr.py <<EOF || echo "FAILED"
Set h to "Hello"
Set w to "World"
Print h, w
EOF
```

### Interactively

```Text
$../vgr.py
Type 'exit' to exit
vgr> Set h to "Hello"
vgr> Set w to "World"
vgr> Print h, w
Hello World
vgr>
```

The interactive command line supports history, using `Ctrl-R` and the up and down arrows, as well as some basic file commands and a help system. Just type `help` to get more details. (_NB: help is a work in progress_)

For more details on the command line options, send in the `--help` option to get full, up-to-date details.

## Variables, Expressions, and Operators

VGR has a hierarchical, global data model, viewed as variables. Some variables are created and _owned_ by the program, but much of the space belongs to you for use in procedures. These parts of the data model are pre-created, and mostly immutable.

* `args` : list of positional user arguments from the command line
* `env` : an imported view of the environment including `env.OFS` and `env.ORS` used by `Print`.
* `math` : Python math constants such as `math.e` and `math.inf`. Read-only.
* `os` : Operating system constants such as `os.linesep` and `os.extsep`. Read-only.
* `string` : More constants that can be used with string functions, like `string.hexdigits` and `string.ascii_letters`. Read-only.
* `vgr` : Read-only internals, some dynamic, other changed by commands.

Variables are case sensitive.

```Text
vgr> set Five to 5
vgr> set five to 6
vgr> print Five, five, FIVE
5 6 None
```

Variable names are hierachical.

```Text
vgr> set data.Five to 5
vgr> set data.Six to 6
vgr> print data
{'Five': 5, 'Six': 6}
```

Note that you didn't need to create `data` first, and the same goes for deeper hierarchies.

```Text
vgr> set this.is.several.layers.deep = 5
vgr> print this
{'is': {'several': {'layers': {'deep': 5}}}}
```

Print displays these variable paths as a Python dictionary, which is mostly interchangable with a JSON object. Mostly.

Steps in a variable path can be expressed in _snake_ or _kabab_ case.

```Text
vgr> set _this.is-several.layers_._deep_ = 5
vgr> print _this.is-several.layers_._deep_
5
```

Steps in the variable path can contain ASCII alphanumeric characters, and the dash or underscore characters. They can start with an underscore, but not a dash:

```Text
vgr> Set _valid = 0
vgr> Set -not-valid = 0
Set -not-valid = 0
    ^
Unexpected input at line 1, column 5.
Expected NAME.
```

### Removing Values

The Unset statment is used to remove variables.

```Text
vgr> set data.Five to 5
vgr> set data.Six to 6
vgr> print data
{'Five': 5, 'Six': 6}
vgr> unset data.Five
vgr> print data
{'Six': 6}
vgr> unset data.Six
vgr> print data
{}
vgr> unset data
vgr> print data
None
```

If you ask to remove a variable that doesn't exist, or part of its path do not exist, the request is ignored.

## Things like variables, but they aren't

Besides obvious things like keywords in the language, there are some names that look like variables but aren't. These are `None`, `Null`, `Inf`, `Nan`, `True`, and `False`. These are used in expressions, but can't be used in variables.

```Text
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

```Text
vgr> Set h to "Hello"
vgr> Set w to "World"
vgr> Print h, w
Hello World
```

Invoking `Print` without argument will just create a blank line... but not always. `Print` works like AWK, which means that items separated by commas get a _output field separator_ (OFS) placed between them and and an _output record separator_ (ORS) at the end. In VGR, as with awk, these values are stored in `env.OFS` and `env.ORS`:

```Bash
export OFS=" | "
vgr -e 'Set a to 5; Set b to 6; Print a, b'
5 | 6
```

Or you can change them at runtime:

```Text
vgr> Set env.OFS = " | "
vgr> Set env.ORS = " |\n"
vgr> Print "Hello", "World"
Hello | World |
 ```

You need to add the `\n` to get a newline in your record separator if you don't want the text to bunch up.

If you set either separators to an empty string or to `None` the default values of a space and a newline will be used.

### Printf Statement

`Printf` uses [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings) to format data. The first argument is the format string, which may require additional expression depending upon its contents.

```Text
vgr> Set h to "Hello"
vgr> Set w to "World"
vgr> Printf "{} {}!\n", h, w
Hello World!
vgr> Printf "{1}, {0}?\n", w, h
Hello, World?
```

`Printf` does not use the field or record separators, and if you want a newline printed at the end, it must be provided either in the format string or as part of the arguments.

### Exhibit Statement

`Exhibit` is inspired by COBOL and displays information about variables. When looking at a single value, there is little difference from using `Print`:

```Text
vgr> Print h
Hello
vgr> Exhibit h
h = 'Hello'
```

You can see a bigger difference when printing variables that are dictionaries:

```Text
Print math
{'pi': 3.141592653589793, 'e': 2.718281828459045, 'tau': 6.283185307179586, 'inf': inf, 'nan': nan, 'neg_inf': -inf, 'float': {'max': 1.7976931348623157e+308, 'min': 2.2250738585072014e-308}, 'random': 0.8042746395530653, 'random100': 97}
vgr> Exhibit math
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

## Expressions and Operators

Much of what you will need to do in VGR relies on expressions. These can be simply the names of variables, data from Vault, or strings and numbers.

If you've every done any coding you'll recognize many of the items that are found in expressions:

* **Number constants** : either integer or floating point values. Number can be expressed in hexidecimal (`0x2a`), octal (`0o52`), or binary (`0b101010`) as well a decimal values. `Inf` represents infinity and `NaN` for not-a-number.
* **String constants** : simply quoted strings with traditional backslash escapes as well as escaped Unicode values.
* **Boolean constants** : `True` and `False`, no quotes.
* **Special constants** : `None` and `Null`, which are equivalent.
* **Arrays** : Arrays themsleves are composed of expressions which may be constants or computed values. Arrays are hetrogenous and can be nested:

```Text
vgr> set foo = 5
vgr> set bar = 3
vgr> set foo_bar = [ foo, bar, "foo", "bar" ]
vgr> print foo_bar
[5, 3, 'foo', 'bar']
vgr> set foo_bar = [ [foo, bar], ["foo", "bar"] ]
vgr> print foo_bar
[[5, 3], ['foo', 'bar']]
```

Armed with variables and values you can create complicated expressions that test conditions and transform results.

### Operators

Operators are used to conpare and transform values. Many are arithmetic operations while others are string or array oriented. Arithmetic operations work primarily with numbers, but are polymorphic. They'll do their best to intuit the request based on the data types involved; we'll look at that in a bit.

The basic arithmetic operations are:

* Addition, Sutraction, Multiplication, and Division: Unsurprisingly these are `+`, `-`, `*`, and `/` respectively, although you can use fancy Unicode values like `÷` and `×` too.
* _Floor Division_ : `//` returns an integer result of division
* Modulo : `%`
* Raising to a power : `**`
* [Bitwise AND](https://en.wikipedia.org/wiki/Bitwise_operation#AND), [Bitwise OR](https://en.wikipedia.org/wiki/Bitwise_operation#OR), and [Bitwise XOR](https://en.wikipedia.org/wiki/Bitwise_operation#XOR) : These use `&`, `|`, and `^` respectively.
* [Bit Shifting](https://en.wikipedia.org/wiki/Bitwise_operation#Shift_operations) : use `<<` for left shift and `>>` for right shift.

```Text
vgr> set x = 5
vgr> set y = 3
vgr> set env.OFS=" | "
vgr> print x + y, x - y, x / y, x // y, x % y
8 | 2 | 1.6666666666666667 | 1 | 2
vgr> printf "x={:b}, y={:b} : {:b} | {:b} | {:b} |\n", x, y, x & y, x | y, x ^ y
x=101, y=11 : 1 | 111 | 110 |
vgr> print x >> 1, y << 2
2 | 12
```

Comparison operations work with both numeric and non-numeric data.

* Equality : use `==`, `Equals`, `Is`, `Is Equal To`
* Inequality : use `!=`, `<>`, `Is Not`, `Is Not Equal To`
* Less Than : use `<` or `Is Less Than`
* Greater Than : use `>` or `Is Greater Than`
* Less Than or Equal To : use `<=` or `Is Not Greater Than`
* Greater Than or Equal To : use `>=` or `Is Not Less Than`

In the longer text versions, the `Is` is optional, and in all words can be in any mixture of upper and lower case. Results of comparison operations are always `True` or `False`.

```Text
vgr> set x = 5
vgr> set y = 3
vgr> set env.OFS=" | "
vgr> print x == y, x != y, x < y, x > y, x <= y, x >= y
False | True | False | True | False | True
```

### Operator Precedence and Parentheses

Use parentheses if explicit order of evaluations is required.

```Text
vgr> set x = 5
vgr> set y = 3
vgr> set env.OFS=" | "
vgr> print x * y + 2, (x * y) + 2, x * (y + 2)
25 | 17 | 25
```

### Whitespace in Expressions

Typically whitespace, spaces, tabs, newlines, etc, are not important in expressions. However, difficulty may arise with the use of signed numbers, and while using parentheses solves the problem, using spaces around operators is encouraged on functional and aesthetic grounds.

```Text
vgr> print x*y+2,x*y-2
print x*y+2,x*y-2
               ^
Unexpected input at line 1, column 16.
vgr> print x*y+2,x*y- 2
25 | 5
vgr> print x * y + +2, x * y - -2
25 | 25
```

### String and List Operators

* `Is In` and `Is Not In` : is the left-side value present in the right-side value or not
* `Contains` and `Does Not Contain` : is the right-side value present in the left-side or not; effectively the reverse of In
* `Match` and `Does Not Match` : TBD. You can also use `~` and `!~` respectively

There are also `IMatch` versions that performs comparisons indepent of case

## Comments

True to its polyglot nature, three different commenting styles are available and may be freely intermixed.

* SQL Style : Comments start with `--`
* Shell Style : Comments start with `#`
* 'C', Java, et al Style : Comments start with `//` or blocks between `/*` and `*/`

```Text
# Just like in Shell Scripts, AWK, or Python...
      // Or back in 'C' and Java
-- SQL-ish too
Set x to 42 # This is fine
Set x /* comment */ to /* again */ 42
```

## Statements

Several statements have already been discussed and demonstrated: `Set`, `Print`, `Printf` and `Exhibit`. And if you've used the interactive interface you've likely used `Exit`. Here we'll cover the remaining statments, and especially `Select`.

### Runtime Control Options

There are three statements that change the behavior of subsequent statements.

* `Debug` : prints technical information to stderr during execution. Its use is self explanitory.
* `Echo` : prints the command to stderr prior to execution. Useful for debugging and logging. Off by default.
* `Verbose` : prints additional information to stderr during execution. Useful for detailed logging. Off by default.

These statements take an optional expression which is evaluated as a boolean. If no expression is provided, the control is turned on.

```Text
vgr> Echo; Verbose;
Verbose;
Verbose = True
vgr> Print vgr.echo, vgr.verbose
Print vgr.echo, vgr.verbose
True True
vgr> Verbose False; Echo 0;
Verbose False;
```

### Exit and Assert

Exit terminates the application unconditionally, while Assert does so only if a condition check fails.

* `Exit` : terminate with a zero return code
* `Exit expression` : terminate with the exit code given by the expression. Non-numeric results are turned into booleans using Python's "trutiness" rules.

```Text
./vgr.py -e "Exit" && echo "Exited"
Exited
./vgr.py -e "Exit 17" || echo $?
17
```

* `Assert` : unconditional exit with a return code of one
* `Assert expression` : if the expression resolves to a False value, the application exits with a return code of one. An error message is printed.
* `Assert expression : message...` : This acts like _if not this, then printf the message and exit_. We'll demonstrate.

```Text
vgr> Set Limit to Inf
vgr> Assert Limit Less Than (64 * 1024)
Line 1: Assert Limit Less Than (64 * 1024) failed
$ echo $?
1
```

With a message you can customize the output

```Text
vgr> Set Limit to Inf
vgr> Assert Limit Less Than (64 * 1024) : "The Limit was set to {}, which is too high!", Limit
Line 1: The Limit was set to inf, which is too high!
```

### Open and Close

`Open` and `Close` are used to direct the output of statements to files. While you can always use standard I/O redirection, these statements allow you to, for example, run multiple `Selects` and place the results in multiple files.

Two types of output, or streams, are defined: `Output` and `Error`. These have aliases of `Stdout` and `Stderr` respectively. The resulting output of statements like `Print`, `Printf`, and `Select` go to the **output stream**. Output generated by `Exhibit` and `Assert`, as well as that resulting from `Debug`, `Echo`, or `Verbose` being active, goes to the **error stream**.

* `Open` _stream_ expression : opens the file named by the expression for output in Overwrite mode.
* `Open` _stream_ expression _mode_ : open the file with a specific mode. See below for details.
* `Close` _stream_ : closes the stream. If one was never opened, the statement has no effect.

#### Open Mode

Three types of open mode are available:

* `Append` or `Extend` : if the file exists, output is added to it; if not the file is created
* `Overwrite` : the file if it exists is overwritten. This is the default mode used when a mode is not specified.
* `No Overwrite` : if the file exists it is not overwritten. An error message is printed and the application exits with an error code.

When VGR exits, all opened files are closed automatically.

> **Pro Tip…**
>
> The stream name can be followed by an optional `File` keyword for readability.
>
> ```Text
> Open Output File "out.dat"
> // ...
> Close Output File
> ```
>
> Additionally you can use the Python file mode shorthands `A`, `W`, and `X` for the file mode.
>
> ```Text
> Open stdout out_name + ".dat" X
> ```
>
> These are keywords and should not to be quoted.

### Create ZIP

After you've generated output files from statements, you can use VGR to create a ZIP file. The syntax is similar to `Open`, but you do need to specify what will be added to the file.

```Text
Create ZIP expression options...
```

The options can be specified as many times as you need or want.

* `Include` _expression_... : a list of expressions that specify the archive's content. You can use a long space separated list or use Include multiple times.
* `Exclude` _expression_... : a list of expressions that define patterns of exclusion from the archive's content. Like with Include, you can use one line or many.
* `Comment` _expression_ : a comment that will be added to the archive
* `Password` _expression_ : a password to secure the archive _**NOT WORKING ATM; NEED TO REPLACE ZIP MODULE**_

Let's take a look at an example:

```Text
Create ZIP File "reports.zip"
  // All of our output
  Include "out",
  Include "*.csv" "*.json",
  Exclude "*.log" "*.err",
  // Somday we should add the creator...
  Comment "Today's data!";
```

Assuming that `out` is a directory, the first `Include` will recursively add all files in it to our archive list. Then we add in all CSV and JSON files from the current directory with the next `Include`. The `Exclude` option, which could be the first of the options, is used to remove any files added by an `Include` that match those patterns.

Also note that you can add comments in the middle of the statement, as long as they start at the begining of a line.

If none of the `Include` patterns match, or if an `Exclude` removes everything, an empty archive will be constructed.

> **Pro Tip…**
>
> Let's handle that "someday" in the comment...
>
> ```Text
>  Comment "Report created by " + os.login;
> ```
>
> Don't forget that there are predefined variables with information that you can
> access: use `Exhibit` to see what's available!


### `SetVar()`

`SetVar()` stores intermediate values for later use, often in the same statement. Although it looks like a function, it operates differently. Instead of changing the current result as most functions do, it stores a copy of the results.

The argument is also different: it's not an expression, but a variable name, just like in a `Set` statement.

```Text
vgr> Set email To "robert@SAMPLE.com"
vgr> Print email.Split("@").SetVar(split_email)
      .Item(0).TitleCase()
      + "@" +
      split_email.Item(1).Lower()
Robert@sample.com
```
