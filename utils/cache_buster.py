import random
import string

def cache_buster_value():
    characters = string.ascii_letters
    random_integer = random.randint(100000, 999999)
    random_letters = ''.join(random.choices(characters, k=6))
    
    return f"{random_letters}{random_integer}"
