from types import IntType, LongType, FloatType

def is_number(n):
    return n in (IntType, LongType, FloatType)

def level_string_to_number(string):
    string = string.lower()
    if string == "debug": return 10
    if string == "info": return 20
    if string == "warn": return 30
    if string == "error": return 40
    if string == "fatal": return 50
    return -1

def level_number_to_string(number):
    if number == 10: return "debug"
    if number == 20: return "info"
    if number == 30: return "warn"
    if number == 40: return "error"
    if number == 50: return "fatal"
    return "Unknown (%i)" % (self.level)
