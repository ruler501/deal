import ast

import pytest

from deal.linter._extractors import get_returns


@pytest.mark.parametrize('text, expected', [
    ('return 1', (1, )),
    ('return -1', (-1, )),
    ('return 3.14', (3.14, )),
    ('return -3.14', (-3.14, )),
    ('return "lol"', ('lol', )),
    ('return b"lol"', (b'lol', )),
    ('return True', (True, )),
    ('return None', (None, )),
])
def test_get_returns_simple(text, expected):
    returns = tuple(r.value for r in get_returns(body=ast.parse(text).body))
    assert returns == expected
