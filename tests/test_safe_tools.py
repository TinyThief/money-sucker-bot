import unittest
from typing import Never

from utils.safe_tools import safe_execute


def good_function(x):
    return x * 2


def bad_function(x) -> Never:
    msg = "Ошибка в функции"
    raise ValueError(msg)


class TestSafeExecute(unittest.IsolatedAsyncioTestCase):
    async def test_successful_execution(self) -> None:
        result = await safe_execute(good_function, 5)
        assert result == 10

    async def test_failed_execution_returns_none(self) -> None:
        result = await safe_execute(bad_function, 5)
        assert result is None


if __name__ == "__main__":
    unittest.main()
