from types import IntType, LongType, FloatType

def is_number(n):
    return n in (IntType, LongType, FloatType)
