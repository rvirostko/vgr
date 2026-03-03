# Guidelines

## Arithmetic Operations and Functions

* Operations between types should follow Python rules as closely as possible
* None as the primary input should be treated as zero

  ```None op Any ⇔ 0 op Any```

  or a matching equivalent, such as an empty collection

* If an operation is commutative, None as the secondary input should return _None_

  ```_Any_ + None   → None```

* Arithmetic operations can work with strings, which are cast compatibly
* Operations should be distributive over list and tuple
