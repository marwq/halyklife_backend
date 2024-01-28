import random

with open('bep39.txt') as f:
    words = f.read().splitlines()

def random_sentence(len_: int = 8):
    return ' '.join(random.choice(words) for _ in range(len_))