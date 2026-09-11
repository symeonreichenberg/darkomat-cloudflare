import hmac

from js import Buffer, Object, TextEncoder, Uint8Array, crypto
from pyodide.ffi import to_js as _to_js


def to_js(value):
    return _to_js(value, dict_converter=Object.fromEntries)


PASSWORD_ITERATIONS = 600_000
SALT_LENGTH = 16
KEY_LENGTH_BITS = 256

encoder = TextEncoder.new()


async def hash_password(password: str) -> str:
    """
    Create a PBKDF2-HMAC-SHA256 password hash.

    Stored format:
    pbkdf2_sha256$600000$<salt-base64>$<hash-base64>
    """

    salt = Uint8Array.new(SALT_LENGTH)
    crypto.getRandomValues(salt)

    password_data = encoder.encode(password)

    key = await crypto.subtle.importKey(
        "raw",
        password_data,
        to_js({"name": "PBKDF2"}),
        False,
        ["deriveBits"],
    )

    derived = await crypto.subtle.deriveBits(
        to_js({
            "name": "PBKDF2",
            "salt": salt,
            "iterations": PASSWORD_ITERATIONS,
            "hash": "SHA-256",
        }),
        key,
        KEY_LENGTH_BITS,
    )

    salt_b64 = Buffer.from(salt).toString("base64")
    hash_b64 = Buffer.from(derived).toString("base64")

    return (
        f"pbkdf2_sha256${PASSWORD_ITERATIONS}"
        f"${salt_b64}${hash_b64}"
    )


async def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against a stored PBKDF2 hash.
    """

    try:
        algorithm, iterations, salt_b64, expected_hash_b64 = (
            stored_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations)

        salt = Buffer.from(salt_b64, "base64")

        password_data = encoder.encode(password)

        key = await crypto.subtle.importKey(
            "raw",
            password_data,
            to_js({"name": "PBKDF2"}),
            False,
            ["deriveBits"],
        )

        derived = await crypto.subtle.deriveBits(
            to_js({
                "name": "PBKDF2",
                "salt": salt,
                "iterations": iterations,
                "hash": "SHA-256",
            }),
            key,
            KEY_LENGTH_BITS,
        )

        actual_hash_b64 = Buffer.from(derived).toString("base64")

        return hmac.compare_digest(
            actual_hash_b64,
            expected_hash_b64,
        )

    except (ValueError, TypeError):
        return False