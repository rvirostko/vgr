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
import copy

from .mathpak import poly_repr

# These values are INTENTIALLY omitted from keys()!
GOBAL_CONTEXT = '$global'
OUTER_CONTEXT = '$outer'
LOCAL_CONTEXT = '$local'
STATIC_CONTEXT = '$static'
_CONTEXT_KEYS = [GOBAL_CONTEXT, OUTER_CONTEXT, LOCAL_CONTEXT, STATIC_CONTEXT]

MAX_FRAMES = 64

class DataDictionary():
    """
    A hierachical data store
    """

    def __init__(self):
        # Populate the stack of frames with our "global" frame
        self._frames: list[Frame] = [Frame()]
        self._immutable_prefixes: set = set()
        for context in _CONTEXT_KEYS: self.add_immutable_prefix(context)

    def add_immutable_prefix(self, prefix: str) -> None:
        """Immutable prefixes means you can't change any part of them"""
        self._immutable_prefixes.add(self._assert_valid_prefix(prefix))

    def _assert_valid_prefix(self, prefix: str) -> str:
        """Prefixes cannot contain "." or be a reserved word"""
        assert prefix and '.' not in prefix, "Invalid prefix"
        return prefix

    def push_frame(self, locals_list: list=None) -> None:
        if len(self._frames) > MAX_FRAMES: raise RecursionError(f'Too many Frames: {MAX_FRAMES}')
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
        assert len(self._frames) > 1
        dropped_frame = self._frames.pop()
        dropped_frame.drop()

    @property
    def in_local_frame(self) -> bool:
        """
        Is the current frame a _local_ frame vs the _global_ frame?

        :return: True if the current frame is a local frame
        :rtype: bool
        """
        return len(self._frames) > 1

    @property
    def _current_frame(self) -> "Frame":
        """The frame at the end of the list is the current frame"""
        return self._frames[-1]

    @property
    def _global_frame(self) -> "Frame":
        """The frame at the head of the list is the global frame"""
        return self._frames[0]

    def keys(self) -> list[str]:
        """Return all the top-level keys in the dictionary"""
        keys = set()
        f = self._current_frame
        while f is not None:
            keys.update(f.keys())
            # NB: the fact that I have to ignore this shows that pylint,
            #     like other "linters" have a limited understanding of
            #     object oriented models
            f = f.outer_frame() # pylint: disable=assignment-from-none
        return [*keys]

    def reset(self) -> None:
        """
        Removes everything outside of immutable prefixes
        """
        self._current_frame.reset(self._immutable_prefixes)

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
                if step in _CONTEXT_KEYS:
                    raise ValueError(f'Improper use of {step!r} variable context')
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
                if step in _CONTEXT_KEYS:
                    raise ValueError(f'Improper use of {step!r} variable context')
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
Declares a variable in the appropriate frame.

Returns :
* _True_ if variable established as local
* _False_ if variable established as global
* _None_ if variable pre-existing

The value at the path will be set to _None_ if
nothing already exists; existing values are never
overwritten.
"""
        if len(self._frames) == 1 and as_local:
            raise ValueError('Local is invalid used in this context')
        # Use current frame if local required or no preference
        target_frame = self._current_frame if as_local is None or as_local else self._global_frame
        # We anchor the path in the frame
        rc = target_frame.declare(path[0])
        # Then we can set its value if it was not already present
        if rc is not None: self.set_var(None, *path)
        return rc

    def _resolve_context(self, frame: "Frame", *path: str) -> tuple:
        """
        Handles initial deref of $global/$outer/$local/$static in paths for reads.
        Writes are prohibited, so not used there.
        """
        context: str = path[0]
        # $static is TBD/reserved; always None
        if context == STATIC_CONTEXT: return (context, None, path[1:])
        # $local means data rooted in a non-global frame
        if context == LOCAL_CONTEXT:
            return (context, frame.data if frame != self._global_frame else None, path[1:])
        # $global means data only available in the global frame
        if context == GOBAL_CONTEXT: return (context, self._global_frame.data, path[1:])
        # $outer is contextual and not always available
        if context == OUTER_CONTEXT:
            outer = frame.outer_frame()
            return (context, (outer.data if outer is not None else None), path[1:])
        # No context, so we let the Frame's logic handle it
        return (None, frame, path)

    def get_var(self, *path: str) -> Any:
        """
        Called with vetted user args or can be called directly.
        Returns the values stored on the path, or None if the
        path does not lead to a dictionary.
        Note that "None" is not a definitive "not found" statement.
        """
        is_immutable = False
        context, data, path = self._resolve_context(self._current_frame, *path)
        if not path: raise ValueError(f'Missing variable name after {context!r}')
        if data is not None:
            is_immutable = path[0] in self._immutable_prefixes
            for step in path:
                if step in _CONTEXT_KEYS:
                    raise ValueError(f'Improper use of {step!r} variable context')
                if not isinstance(data, (Frame, dict)) or step not in data: return None
                data = self._value_for(data[step])
        return copy.deepcopy(data) if is_immutable else data

    def var_exists(self, *path: str) -> tuple[bool, str, Any]:
        """
        Returns a tuple that says if the value exists and,
        if it does, what that value is.
        """
        _, data, path = self._resolve_context(self._current_frame, *path)
        true_name = '.'.join(path)
        if data is None: return (False, true_name, None)
        if path:
            for step in path:
                if step in _CONTEXT_KEYS:
                    raise ValueError(f'Improper use of {step!r} variable context')
                if not isinstance(data, (Frame, dict)) or step not in data: return (False, true_name, None)
                data = self._value_for(data[step])
        else:
            data = self._value_for(data)
        return (True, true_name, data)

    @staticmethod
    def valid_path_step(step: str) -> str:
        if step is None or not isinstance(step, str) or all(sc.isspace() for sc in step):
            raise ValueError(f'Invalid name component: {step!r}')
        return step

    def validate_user_set_path(self, *path: str) -> tuple:
        """
        Check the path for validity in setting, preventing alterations immutable areas
        """
        prefix: str = path[0]
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
    def __repr__(self): return poly_repr(self._func())
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

    def outer_frame(self) -> "Frame":
        return None

    @property
    def data(self) -> dict:
        return self._data

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

    def reset(self, immutable_prefixes: tuple) -> None:
        for key in list(self._data):  # list() to avoid dict size change during iteration
            if key not in immutable_prefixes: del self._data[key]

    def __iter__(self): return iter(self._data)
    def __getitem__(self, key: str) -> Any: return self._data[key]
    def __setitem__(self, key: str, value: Any) -> None: self._data[key] = value
    def __delitem__(self, key: str) -> None: del self._data[key]
    def __contains__(self, key: str) -> bool: return key in self._data
    def __repr__(self) -> str: return f'{self.__class__.__name__}({self._data!r})'
    def __str__(self) -> str: return str(self._data)

    def keys(self) -> KeysView[str]:
        """
        By design, this returns _only_ the keys defined
        in this frame, not the chain of outer frames
        """
        return self._data.keys()

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
    def __init__(self, outer_frame: Frame, locals_list: list=None) -> None:
        super().__init__(locals_list)
        self._outer_frame: Frame = outer_frame

    def outer_frame(self) -> Frame:
        return self._outer_frame

    def declare(self, prefix: str) -> bool:
        rc = super().declare(prefix)
        return None if rc is None else True # indicates it is a local

    def drop(self) -> None:
        try:
            super().drop()
        finally:
            self._outer_frame = None

    def reset(self, immutable_prefixes: tuple) -> None:
        # First the locals
        super().reset(immutable_prefixes)
        # then everything else
        self._outer_frame.reset(immutable_prefixes)

    def __iter__(self) -> Iterator:
        seen = set()
        # First the locals
        for key in self._data:
            yield key
            seen.add(key)
        # then everything else
        for key in self._outer_frame:
            if key not in seen:
                yield key

    def __getitem__(self, key: str) -> Any:
        # locals shadow outer frames' variables
        return self._data[key] if key in self._data else self._outer_frame[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self._data or key not in self._outer_frame:
            # already a local or not in outer frames (a new local)
            self._data[key] = value
        else:
            self._outer_frame[key] = value

    def __delitem__(self, key: str) -> None:
        # NB: unsetting a local can expose variables in the outer frames
        if key in self._data:
            del self._data[key]
        else:
            del self._outer_frame[key]

    def __contains__(self, key: str) -> bool:
        # First locals, then the outer frames
        return key in self._data or key in self._outer_frame

    def setdefault(self, key: str, default: Optional[Any] = None) -> Any:
        """
        This is called when we are looking for the root of a path for modification.
        """
        # If we dont have it, we need to see if outer frames have it
        if key not in self._data:
            # If a outer frame has it, let them handle it
            if key in self._outer_frame: return self._outer_frame.setdefault(key, default)
            # A new variable, so it becomes a local
            self._data[key] = default
        return self._data[key]

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        if key in self._data:
            return self._data.get(key, default)
        return self._outer_frame.get(key, default)

    def pop(self, key: str, default: Optional[Any] = None) -> Any:
        if key in self._data:
            return self._data.pop(key, default)
        return self._outer_frame.pop(key, default)
