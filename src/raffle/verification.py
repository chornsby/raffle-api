import secrets


def generate_verification_code(population: str, k: int) -> str:
    """Return a somewhat human-readable verification code.

    This is like a password for the user, so it must not be stored as-is.
    """
    return "".join(secrets.choice(population) for _ in range(k))
