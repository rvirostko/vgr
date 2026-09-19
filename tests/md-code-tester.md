# Code block tests

This is a visual test to see if extensions are contributing a "language" to code blocks


### Python

Working. Likely built-in to Markdown

```python
def myFunc(a, b):
    return a + b
```

### VGR

Not working. Tested as a locally installed extension.

```
Define Function myFunc(a, b)
    Return a + b
End-Function
```

### Lark

Not working. Tested as an installed 3rd party extension.

```lark
unless_statement: "Unless"i expr _CLAUSE_SEP? statement+ ("End-Unless"i | "End"i) -> unless
```

### 'C'

Working. Likely built-in to Markdown

```c
int my_func(int a, int b) {
    return(a + b);
}
```
