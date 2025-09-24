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
**Generate a hex checksum for a value**

* _value_.Checksum()
* _value_.Checksum(_expression_)

The optional expression is the algorithm to use, defaulting to _md5_.
Available algorithms are: _md5_, _sha1_, _sha224_, _sha256_, _sha384_,
_sha512_, _blake2b_, _blake2s_, _sha3_224_, _sha3_256_, _sha3_384_,
_sha3_512_, _shake_128_, and _shake_256_.

If value is an array, the operation is distributed over the array,
returning an array of the checksums.
If the value is a dictionary, it is formated as compact JSON with
sorted keys to create a string for computation.
Other non-string types are converted to a string before computation.

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
        return type(x)(poly_checksum(x1, algo) for x1 in x)
    if isinstance(x, dict):
        x = json.dumps(x, sort_keys=True, indent=None, separators=(',', ':'))
    if not isinstance(x, str): x = str(x)
    hasher.update(x.encode("utf-8"))
    return hasher.hexdigest()
