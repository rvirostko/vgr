"""
The DataDictionary holds hierarchical data used by the application.
Most of the space is avaialble for the user's application, but parts--typically constants--
are immutable.
"""

from typing import (
    Any,
    Dict,
    Iterator,
    KeysView,
    Optional,
)

class DataDictionary():
    """
    A hierachical data store
    """

    # These can't appear in a path name (to prevent confusion)
    _RESERVED_WORDS = ('true', 'false', 'none', 'null')

    def __init__(self):
        # Populate the stack of frames with our "global" frame
        self._frames: list[Frame] = [Frame()]
        self._immutable_prefixes: set = set()
        self._protected_prefixes: set = set()

    def add_immutable_prefix(self, prefix: str) -> None:
        """Immutable prefixes means you can't change any part of them"""
        self._immutable_prefixes.add(self._assert_valid_prefix(prefix))

    def add_protected_prefix(self, prefix: str) -> None:
        """Protected prefixes means you can change any part of them, but not at the top-level"""
        self._protected_prefixes.add(self._assert_valid_prefix(prefix))

    def _assert_valid_prefix(self, prefix: str) -> str:
        """Prefixes cannot contain "." or be a reserved word"""
        assert prefix and '.' not in prefix and prefix not in self._RESERVED_WORDS, "Invalid prefix"
        return prefix

    def push_frame(self, locals_list: list=None) -> None:
        if len(self._frames) >= 8192: raise RecursionError()
        new_frame = LocalsFrame(self._current_frame, locals_list)
        self._frames.append(new_frame)
        try:
            # Fully populate the local variables
            if locals_list:
                for local in locals_list:
                    self.set_var(local[1], *local[0])
        except Exception as e:
            self.pop_frame()
            raise e

    def pop_frame(self) -> None:
        if len(self._frames) <= 1: raise RuntimeError('Frame underflow')
        dropped_frame = self._frames.pop()
        dropped_frame.drop()

    @property
    def _current_frame(self) -> "Frame":
        """The frame at the end of the list is the current frame"""
        return self._frames[-1]

    @property
    def _global_frame(self) -> "Frame":
        """The frame at the head of the list is the global frame"""
        return self._frames[0]

    def keys(self):
        """Return all the top-level keys in the dictionary"""
        return self._current_frame.keys()

    def reset(self) -> None:
        """
        Removes:
        * Everything outside of immutable and protected prefixes
        * Contents of protected prefixes
        """
        self._current_frame.reset(self._protected_prefixes, self._immutable_prefixes)

    def set_var_user(self, value: Any, /, *path: str) -> Any:
        """
        *Deprecated*
        Set an item within the dictionary.
        This is a method to call with user input.
        Returns the value passed in.
        """
        return self.set_var(value, *self.validate_user_set_path(*path))

    def set_var(self, data: Any, /, *path: str) -> Any:
        """
        Called with vetted user args or can be called directly.
        Returns the value passed in.
        """
        current = self._current_frame
        # optimizing for this case prevents the possible
        # deepcopy of something we are about to overwrite
        # when working in a local frame
        if len(path) > 1:
            for step in path[:-1]:
                # If the next step doesn't exist, create it as a dictionary
                next_step = current.setdefault(step, {})
                # If it isn't a dictionary, it has to become one
                if not isinstance(next_step, (Frame, dict)):
                    next_step = {}
                    current[step] = next_step
                current = next_step
        # Last step in the path gets the data
        current[path[-1]] = data
        return data

    def unset_var(self, *path: str) -> Any:
        """
        Called with vetted user args or can be called directly.
        Returns the value removed.
        Note that "None" is not a definitive "not found" statement.
        """
        current = self._current_frame
        if len(path) > 1:
            for step in path[:-1]:
                # If the next step doesn't exist, or is
                # not a dictionary, we can't go anywhere
                # to unset something
                next_step = current.get(step, None)
                if not isinstance(next_step, (Frame, dict)): return None
                current = next_step
            # Last step in the path gets removed
        return current.pop(path[-1], None)

    def declare_var(self, as_local: bool, *path: str) -> bool:
        """
        Declares a variable in the appropriat frame.
        Returns _True_ if the declaration was local.
        The value at the path will be set to _None_ if
        nothing already exists; existing values are never
        overwritten.
        """
        target_frame = self._current_frame
        # If global and more than the global frame
        if not as_local and len(self._frames) > 1:
            # Remove prefix from the current frame if it exists
            # which clears the way for global access
            target_frame.remove(path[0])
            # Switch over to the global frame for the declaration
            target_frame = self._frames[0]
        # We anchor the path in the frame
        rc = target_frame.declare(path[0])
        # Then we can set its value if it was not already present
        if rc is not None: self.set_var(None, *path)
        return rc

    def get_var(self, *path: str) -> Any:
        """
        Called with vetted user args or can be called directly.
        Returns the values stored on the path, or None if the
        path does not lead to a dictionary.
        Note that "None" is not a definitive "not found" statement.
        """
        data = self._current_frame
        for key in path:
            if not isinstance(data, (Frame, dict)) or key not in data: return None
            data = self._value_for(data[key])
        return data

    def var_exists(self, *path: str) -> tuple[bool, Any]:
        """
        Returns a tuple that says if the value exists and,
        if it does, what that value is.
        """
        if not path: return (False, None)
        data = self._current_frame
        for key in path:
            if not isinstance(data, (Frame, dict)) or key not in data: return (False, None)
            data = data[key]
        return (True, self._value_for(data))

    @staticmethod
    def valid_path_step(step: str) -> str:
        if step is None or not isinstance(step, str) or all(sc.isspace() for sc in step):
            raise ValueError(f'Invalid name component: {step!r}')
        if step.lower() in DataDictionary._RESERVED_WORDS:
            raise ValueError(f'{step!r} is a reserved word')
        return step

    def validate_user_set_path(self, *path: str) -> tuple:
        """Check the path for validity in setting, preventing alterations of protected and immutable areas"""
        prefix: str = path[0]
        # protected means you can't change at the top level, but
        # you can change its properties
        if len(path) == 1 and prefix in self._protected_prefixes:
            raise ValueError(f'Cannot alter protected prefix {prefix!r}')
        # immutable means just that
        if prefix in self._immutable_prefixes:
            raise ValueError(f'Cannot alter {".".join(path)!r} - {prefix!r} is immutable')
        return path

    def _value_for(self, data: Any) -> Any:
        """
        Allows us to dereferce executable items stored in the dictionary.
        """
        return data() if callable(data) and not isinstance(data, type) else data

class DynamicValue:
    """
    Wrapper around a lambda (or other no-args function) that can be
    added to the DataDictionary.
    This causes str() and repr() of the value outside of the context
    of lookup where value_for() is used on it to behave in a
    non-astonishing manner.
    """
    def __init__(self, func):
        if not callable(func): raise TypeError("Expected a callable")
        self._func = func

    def __call__(self, *args, **kwargs): return self._func(*args, **kwargs)

    def __add__(self, other): return self._func() + other
    def __bool__(self): return bool(self._func())
    def __complex__(self): return complex(self._func())
    def __eq__(self, other): return self._func() == other
    def __float__(self): return float(self._func())
    def __ge__(self, other): return self._func() >= other
    def __getitem__(self, key): return self._func()[key]
    def __gt__(self, other): return self._func() > other
    def __int__(self): return int(self._func())
    def __iter__(self): return iter(self._func())
    def __le__(self, other): return self._func() <= other
    def __len__(self): return len(self._func())
    def __lt__(self, other): return self._func() < other
    def __mul__(self, other): return self._func() * other
    def __ne__(self, other): return self._func() != other
    def __radd__(self, other): return other + self._func()
    def __repr__(self): return repr(self._func())
    def __rmul__(self, other): return other * self._func()
    def __rsub__(self, other): return other - self._func()
    def __rtruediv__(self, other): return other / self._func()
    def __str__(self): return str(self._func())
    def __sub__(self, other): return self._func() - other
    def __truediv__(self, other): return self._func() / other

class Frame:
    """
    A wrapper around a dictionary represents a _frame_ of data belonging to
    some scoping of data. Initially, there is the global frame, then as
    scope is established, new frames are linked into a chain.
    """
    def __init__(self, locals_list: list=None) -> None:
        self._data: Dict[str, Any] = {}
        # In this way we make sure the frame
        # has these items rooted in it regardless
        # of the design. The caller is responsible
        # for the full population of value using the
        # correct methods.
        if locals_list:
            for prefix in [local[0][0] for local in locals_list]:
                self.declare(prefix)

    def declare(self, prefix: str) -> bool:
        """
        Idempotent if already present.
        Returns _True_ if the variable is a global.
        Returns _None_ if no action taken (already present)
        """
        if prefix in self._data: return None
        self._data[prefix] = None
        return False # indicates it is a global

    def remove(self, prefix: str) -> bool:
        if prefix not in self._data: return False
        del self._data[prefix]
        return True

    def drop(self) -> None:
        self._data.clear()
        self._data = None

    def reset(self, protected_prefixes: tuple, immutable_prefixes: tuple) -> None:
        for key in list(self._data):  # list() to avoid dict size change during iteration
            if key in protected_prefixes:
                self._data[key] = {}
            else:
                if key not in immutable_prefixes:
                    del self._data[key]

    def __iter__(self): return iter(self._data)
    def __getitem__(self, key: str) -> Any: return self._data[key]
    def __setitem__(self, key: str, value: Any) -> None: self._data[key] = value
    def __delitem__(self, key: str) -> None: del self._data[key]
    def __contains__(self, key: str) -> bool: return key in self._data
    def __repr__(self) -> str: return f'{self.__class__.__name__}({self._data!r})'
    def __str__(self) -> str: return str(self._data)

    def keys(self) -> KeysView[str]: return self._data.keys()

    def setdefault(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data.setdefault(key, default)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data.get(key, default)

    def pop(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data.pop(key, default)

class LocalsFrame(Frame):
    """
    This type of frame has _local_ variables which show others
    in the calling chain. Newly created variables are created as locals.
    """
    def __init__(self, caller_frame: Frame, locals_list: list=None) -> None:
        super().__init__(locals_list)
        self._caller_frame: Frame = caller_frame

    def declare(self, prefix: str) -> bool:
        rc = super().declare(prefix)
        return None if rc is None else True # indicates it is a local

    def drop(self) -> None:
        try:
            super().drop()
        finally:
            self._caller_frame = None

    def reset(self, protected_prefixes: tuple, immutable_prefixes: tuple) -> None:
        # First the locals
        super().reset(protected_prefixes, immutable_prefixes)
        # then everything else
        self._caller_frame.reset(protected_prefixes, immutable_prefixes)

    def __iter__(self) -> Iterator:
        seen = set()
        # First the locals
        for key in self._data:
            yield key
            seen.add(key)
        # then everything else
        for key in self._caller_frame:
            if key not in seen:
                yield key

    def __getitem__(self, key: str) -> Any:
        # locals shadow caller frames' variables
        return self._data[key] if key in self._data else self._caller_frame[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self._data or key not in self._caller_frame:
            # already a local or not in caller frames (a new local)
            self._data[key] = value
        else:
            self._caller_frame[key] = value

    def __delitem__(self, key: str) -> None:
        # NB: unsetting a local can expose variables in the callers
        if key in self._data:
            del self._data[key]
        else:
            del self._caller_frame[key]

    def __contains__(self, key: str) -> bool:
        # First locals, then the callers's
        return key in self._data or key in self._caller_frame

    def setdefault(self, key: str, default: Optional[Any] = None) -> Any:
        """
        This is called when we are looking for the root of a path for modification.
        """
        # If we dont have it, we need to see if callers have it
        if key not in self._data:
            # If a caller frame has it, let them handle it
            if key in self._caller_frame: return self._caller_frame.setdefault(key, default)
            # A new variable, so it becomes a local
            self._data[key] = default
        return self._data[key]

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        if key in self._data:
            return self._data.get(key, default)
        return self._caller_frame.get(key, default)

    def pop(self, key: str, default: Optional[Any] = None) -> Any:
        if key in self._data:
            return self._data.pop(key, default)
        return self._caller_frame.pop(key, default)
