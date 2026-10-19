import hashlib
import random

def get_generator_from_hash(sha256_hex_or_bytes: str):

    seed_int = int(sha256_hex_or_bytes, 16)
    
    rng = random.Random(seed_int)
    return rng

data = b"mit_input_eller_filindhold"
sha256_hash = hashlib.sha256(data).hexdigest()

rng = get_generator_from_hash(sha256_hash)

ints = [rng.randint(100, 64000) for _ in range(5)]
print("Sekvens 1:", ints)

rng_replay = get_generator_from_hash(sha256_hash)
print("Sekvens 2:", [rng_replay.randint(100, 64000) for _ in range(5)])