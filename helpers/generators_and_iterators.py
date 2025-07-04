# GENERATORS & ITERATORS
from collections.abc import Generator, Iterable
from typing import Iterator


# 1) Iteration?
# процесс перебирания чего-либо
# for x in ...?

# 2) Iterable object ->>> его можно перебрать, итерируеремый объект
# File objects ->>>> его можно перебрать
# Lists ---> его можно перебрать
# Str - yes
# dict
# ....
# те, у которых есть метод __iter__()

# ITERATOR
# ANY CYCLE + YIELD IN CYCLE == ITERATOR

def one_ten_iterator():
    # генерирует числа от 1 до 10
    # for number in
    
    counter = 1
    while counter <= 10:
        yield counter
        counter += 1


def names_iterator():
    names = ["OLEG", "IVAN", "TANYA"]
    
    for name in names:
        yield name


my_iterator = one_ten_iterator()

# print(
#     next(my_iterator)
# )
# print(
#     next(my_iterator)
# )
# print(
#     next(my_iterator)
# )


# def magic_iterator():
#     number = 0
#     while True:
#         next_number = yield number
#         number += next_number
#
# iterator = magic_iterator()
# iterator.send(None)
#
# print(iterator.send(10))
# print(iterator.send(70))


# Сделать свой range(...)
def my_range(start: int, end: int) -> int:
    counter = start
    ...

