import bcrypt
import hashlib

def hashBcr(password,salt):
    bytes = password.encode('utf-8')

    if not salt: 
        salt = bcrypt.gensalt()
    else:
        pass

    hash = bcrypt.hashpw(bytes, salt)

    return hash

def hashSha(password):
    hash_object = hashlib.sha256()

    hash_object.update(password.encode('utf-8'))

    hex_dig = hash_object.hexdigest()

    return hex_dig