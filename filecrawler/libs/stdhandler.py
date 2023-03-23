import inspect
from io import StringIO
import sys


class StdHandler:
    """
    A context manager that redirects stdout and stderr to devnull
    Used to supress libmagic error 'lhs/off overflow 4294967295 0'
    https://bugs.astron.com/view.php?id=426
    """
    class _Handler(object):
        def __init__(self, func_name, orig_std):
            self._func_name = func_name
            self._orig_std = orig_std

        def write(self, string):
            if self._func_name in str(inspect.stack()):
                return
            self._orig_std.write(string)

        def flush(self):
            self._orig_std.flush()

    def __init__(self, channels=('stdout', 'stderr',)):
        self._orig = {ch : None for ch in channels}
        self._func_name = inspect.stack()[1].function

    def __enter__(self):
        for ch in self._orig:
            self._orig[ch] = getattr(sys, ch)
            setattr(sys, ch, StdHandler._Handler(self._func_name, self._orig[ch]))

        return self

    def __exit__(self, *args):
        for ch in self._orig:
            setattr(sys, ch, self._orig[ch])

