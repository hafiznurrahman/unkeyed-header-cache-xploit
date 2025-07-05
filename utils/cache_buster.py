import random

def cache_buster():
    random_integer = random.randint(100000, 999999)
    parameter = f"uhcxispoisoning={random_integer}"
    return parameter
