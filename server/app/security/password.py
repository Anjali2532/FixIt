from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    """Hash with a fresh salt; never store the supplied password."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")
    return generate_password_hash(password, method="scrypt")


def verify_password(password, stored_hash):
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False
    try:
        return check_password_hash(stored_hash, password)
    except (ValueError, TypeError):
        return False
