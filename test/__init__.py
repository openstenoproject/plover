import inspect

import pytest

from plover import system
from plover.config import DEFAULT_SYSTEM_NAME
from plover.registry import registry


# Setup registry.
registry.update()
# Setup default system.
system.setup(DEFAULT_SYSTEM_NAME)


def parametrize(tests, arity=None):
    '''Helper for parametrizing pytest tests.

    Expect a list of lambdas, one per test. Each lambda must return
    the parameters for its respecting test.

    Test identifiers will be automatically generated, from the test
    number and its lambda definition line (1.10, 2.12, 3.20, ...).

    If arity is None, the arguments being parametrized will be automatically
    set from the function last arguments, according to the numbers of
    parameters for each test.

    '''
    ids = []
    argvalues = []
    for n, t in enumerate(tests):
        line = inspect.getsourcelines(t)[1]
        ids.append('%u:%u' % (n+1, line))
        argvalues.append(t())
    if arity is None:
        arity = len(argvalues[0])
    assert arity > 0
    def decorator(fn):
        argnames = list(
            parameter.name
            for parameter in inspect.signature(fn).parameters.values()
            if parameter.default is inspect.Parameter.empty
        )[-arity:]
        if arity == 1:
            argnames = argnames[0]
        return pytest.mark.parametrize(argnames, argvalues, ids=ids)(fn)
    return decorator
