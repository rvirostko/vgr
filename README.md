# VGR - Vault Generic Reporting
Working/transfer area for "Vault Generic Reporting"

## Getting started

But first, this important note: **Nothing is yet really hooked up to Vault, so if you expect output... yeah, no.**

There are four ways to run VGR:

### Statements on the command line

  ```
  $./vgr -e 'Print "Hello World"'
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

The interactive command line supports history, using Ctrl-R and the up and down arrows, as well as some basic file commands and a help system. Just type `help` to get more details. (_NB: help is a work in progress_)
