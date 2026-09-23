"""Experimental drop in for re.Pattern"""
import re
from typing import Any, Match, Optional

class VPattern:
    """A drop in replacement for re.Pattern and other re operations"""
    NOFLAG = 0 # our baseline is Python 3.9, so this isn't present
    ASCII = re.ASCII
    DEBUG = re.DEBUG
    DOTALL = re.DOTALL
    IGNORECASE = re.IGNORECASE
    LOCALE = re.LOCALE
    MULTILINE = re.MULTILINE
    VERBOSE = re.VERBOSE

    def __init__(self, pattern: re.Pattern) -> None:
        self._pattern = pattern

    @classmethod
    def compile(cls, pattern: str, flags: int = 0) -> "VPattern":
        return cls(re.compile(pattern, flags))

    @classmethod
    def escape(cls, pattern: Any) -> Any: return re.escape(pattern)

    @classmethod
    def decode_flags(cls, flags: int) -> str:
        rc = ''
        if flags > 0:
            if flags & VPattern.ASCII:      rc += 'a'
            if flags & VPattern.DEBUG:      rc += 'd'
            if flags & VPattern.IGNORECASE: rc += 'i'
            # LOCALE unlikely since it can only be used with bytes
            if flags & VPattern.LOCALE:     rc += 'l'
            if flags & VPattern.MULTILINE:  rc += 'm'
            if flags & VPattern.DOTALL:     rc += 's'
            # NB: template not supported as obsoleted by verbose
            # NB: unicode not supported as it is redundant
            if flags & VPattern.VERBOSE:    rc += 'x'
        return rc

    @classmethod
    def compose_flags(cls, flags: str) -> int:
        rc = VPattern.NOFLAG
        if flags is not None:
            for fc in flags.lower():
                if fc.isspace(): continue
                if   fc == 'a': rc += VPattern.ASCII
                elif fc == 'd': rc += VPattern.DEBUG
                elif fc == 'i': rc += VPattern.IGNORECASE
                # LOCALE unlikely since it can only be used with bytes
                elif fc == 'l': rc += VPattern.LOCALE
                elif fc == 'm': rc += VPattern.MULTILINE
                elif fc == 's': rc += VPattern.DOTALL
                # NB: template not supported as obsoleted by verbose
                # NB: unicode not supported as it is redundant
                elif fc == 'x': rc += VPattern.VERBOSE
                else:           raise ValueError(f'Unknown regular expression pattern flag: {fc!r}')
        return rc

    @classmethod
    def purge_cache(cls) -> None:  re.purge()

    def __str__(self) -> str: return self.pattern

    def __repr__(self) -> str:
        # NB: no need to mess with the pattern for "\/"
        return "r/" + self.pattern + "/" + VPattern.decode_flags(self.flags)

    def __getattr__(self, name: str): return getattr(self._pattern, name)

    def __eq__(self, other: object) -> bool:
        return self._pattern == other._pattern if isinstance(other, VPattern) else NotImplemented

    def __hash__(self) -> int: return hash(self._pattern)

    def __copy__(self) -> "VPattern": return self

    def __deepcopy__(self, _memo: dict[int, Any]) -> "VPattern": return self

    @property
    def pattern(self) -> str: return self._pattern.pattern

    @property
    def flags(self) -> int: return self._pattern.flags

    @property
    def groups(self) -> int: return self._pattern.groups

    @property
    def groupindex(self) -> dict[str, int]: return self._pattern.groupindex

    def search(self, string: str, pos: int = 0, endpos: Optional[int] = None) -> Optional[Match[str]]:
        return self._pattern.search(string, pos) if endpos is None else self._pattern.search(string, pos, endpos)

    def match(self, string: str, pos: int = 0, endpos: Optional[int] = None) -> Optional[Match[str]]:
        return self._pattern.match(string, pos) if endpos is None else self._pattern.match(string, pos, endpos)

    def fullmatch(self, string: str, pos: int = 0, endpos: Optional[int] = None) -> Optional[Match[str]]:
        return self._pattern.fullmatch(string, pos) if endpos is None else self._pattern.fullmatch(string, pos, endpos)

    def split(self, string: str, maxsplit: int = 0) -> list[str]:
        return self._pattern.split(string, maxsplit)

    def findall(self, string: str, pos: int = 0, endpos: Optional[int] = None) -> list:
        return self._pattern.findall(string, pos) if endpos is None else self._pattern.findall(string, pos, endpos)

    def finditer(self, string: str, pos: int = 0, endpos: Optional[int] = None):
        return self._pattern.finditer(string, pos) if endpos is None else self._pattern.finditer(string, pos, endpos)

    def sub(self, repl: str, string: str, count: int = 0) -> str:
        return self._pattern.sub(repl, string, count)

# Held in reserve
#    def subn(self, repl: str, string: str, count: int = 0) -> tuple[str, int]:
#        return self._pattern.subn(repl, string, count)
