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
