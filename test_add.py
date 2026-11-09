import pytest
from add import add

@pytest.mark.parametrize('a, b, expected', [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (10, 15, 25)
])
def test_add(a, b, expected):
    assert add(a, b) == expected
