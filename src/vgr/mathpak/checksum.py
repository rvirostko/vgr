"""
Checksum function
"""

import hashlib
import json

import _hashlib

from .common import str_arg

_DEFAULT_ALGO = 'md5'

def poly_checksum(x, algo: str=_DEFAULT_ALGO) -> str:
    """
**Generate a checksum string for a value**

* Checksum(*value*)
* Checksum(*value*, *algorithm*)
* *value*.Checksum()
* *value*.Checksum(*algorithm*)

If *value* is an array, the operation returns an array of the checksums.
If the value is a dictionary, it is formated as compact JSON with
sorted keys to create a string for computation.
Other non-string types are converted to a string before computation.

The optional *algorithm* defaults to *md5*.
Available algorithms are: *md5*, *sha1*, *sha224*, *sha256*, *sha384*,
*sha512*, *blake2b*, *blake2s*, *sha3_224*, *sha3_256*, *sha3_384*,
*sha3_512*, *shake_128*, and *shake_256*.

```vgr
None.Checksum() → None
"".Checksum() → "d41d8cd98f00b204e9800998ecf8427e"
"Hello".Checksum() → "8b1a9953c4611296a827abf8c47804d7"
"Hello".Checksum("MD5") → "8b1a9953c4611296a827abf8c47804d7"
"Hello".Checksum("sha256") →
    "185f8db32271fe25f561a6fc938b2e264306ec304eda518007d1764826381969"
```
"""
    if x is None: return None
    hasher = None
    if isinstance(algo, _hashlib.HASH):
        hasher = algo.copy()
    else:
        if algo is None:
            hasher = hashlib.new('md5')
        else:
            hasher = hashlib.new(str_arg(algo, 'Algorithm'))
    if isinstance(x, (list, tuple)):
        return list(poly_checksum(x1, algo) for x1 in x)
    if isinstance(x, dict):
        x = json.dumps(x, sort_keys=True, default=str, indent=None, separators=(',', ':'))
    if not isinstance(x, str): x = str(x)
    hasher.update(x.encode("utf-8"))
    return hasher.hexdigest()
