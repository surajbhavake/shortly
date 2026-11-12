import secrets
import string

ALPHABET = string.ascii_letters + string.digits

def generate_slug(length: int = 7) -> str:
    slug = ""

    for i in range(length):
        character = secrets.choice(ALPHABET)
        slug +=character

    return slug