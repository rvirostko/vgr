## Running VGR Scripts

There are multiple ways VGR scripts and commands.

### Statements on the command line

```Bash
vgr --execute 'Print "Hello World"'
Hello World
```

Multiple statements can be specified using semicolons:

```Bash
vgr --execute 'Set h To "Hello"; Set w To "World"; Print h, w'
Hello World
```

While semi-colons between statements are generally optional, they should be used when you have more than one statement per line.

### Statements stored in a file

```Bash
echo 'Print "Hello World"'>hello.txt
vgr --file hello.txt
Hello World
```

Multiple files can be run, with the internal variables and environment shared between them:

```Bash
echo 'Set h to "Hello"; Set w to "World"' > set_vars.txt
echo 'Print h, w' > hello.txt
vgr --file set_vars.txt --file hello.txt
Hello World
```

There is also a `--include` option which works similarly to `--file` but prevents the script from executing more than once. This would typically used by a script that defines shared functions.

Additionally, the settings of variables can be passed in directly, but quotes must be escaped when setting string variables.

```Bash
vgr --assign h=\"Hello\" --assign w=\"World\" --execute "Print h, w"
Hello World
```

### Statements from stdin

```Bash
echo 'Set h to "Hello"; Set w to "World"; Print h, w' | vgr
Hello World
```

### Using 'Here' documents

```Bash
vgr <<EOF || echo "FAILED"
Set h to "Hello"
Set w to "World"
Print h, w
EOF
```

### Interactively: the REPL

```vgr
vgr
Type **exit** to exit
vgr> Set h to "Hello"
vgr> Set w to "World"
vgr> Print h, w
Hello World
vgr>
```

The REPL supports history, using `Ctrl-R` and the up and down arrows, as well as some basic file commands and a help system. Just type `help` to get more details.

For more details on the command line options, use the `--help` option to get full, up-to-date details.

### Multiple input options

More than one form of input can be used at a time. Scripts and statements defined by `--execute`, `--file`, `--include`, and `--assign` are performed in the order provided.

After those sources are complete, if stdin is available, it is read.

The interactive REPL automatically starts if none of the previously
listed options are provided, but it can be forced by using the `--repl` option as long as stdin is interactive.

In this case, the REPL is started after all command line options have completed.
