import os
from typing import Any as TypingAny
from .helpers import helper as local_helper

MY_GLOBAL = 1
OTHER_GLOBAL: str = "two"


class MyClass:
    count = 0
    label: str = "ready"

    class InnerClass:
        inner_value = 3

    def my_method(self) -> int:
        return self.count

    async def my_async_method(self) -> str:
        return self.label


async def top_level_function(value: int) -> int:
    return value + 1
