import hashlib
import hmac
import secrets


PASSWORD_ITERATIONS = 390_000
PASSWORD_SCHEME = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iterations_text, salt, expected_digest = password_hash.split("$", 3)
        iterations = int(iterations_text)
        if scheme != PASSWORD_SCHEME:
            return False
        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            iterations,
        ).hex()
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual_digest, expected_digest)
