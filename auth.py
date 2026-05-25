"""
auth.py - Sistema de autenticación simple
- Almacenamiento de usuarios en JSON
- Contraseñas hasheadas con PBKDF2
- Cada usuario tiene datos separados
"""

import hashlib
import os
import json
from pathlib import Path

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"

def _init_data_dir():
    """Ensure data directory and users file exist."""
    DATA_DIR.mkdir(exist_ok=True)
    if not USERS_FILE.exists():
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)

def _load_users() -> dict:
    """Load all users from JSON file."""
    _init_data_dir()
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def _save_users(users: dict):
    """Save all users to JSON file."""
    _init_data_dir()
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def _hash_password(password: str) -> str:
    """Hash a password with PBKDF2 + random salt. Returns hex string."""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    )
    return (salt + key).hex()

def _verify_password(password: str, stored_hex: str) -> bool:
    """Verify a password against a stored hash."""
    try:
        stored_bytes = bytes.fromhex(stored_hex)
        salt = stored_bytes[:32]
        stored_key = stored_bytes[32:]
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100000
        )
        return key == stored_key
    except (ValueError, IndexError):
        return False

def create_user(username: str, password: str, nombre: str = "") -> tuple[bool, str]:
    """
    Create a new user.
    Returns (success: bool, message: str).
    """
    username = username.strip().lower()
    if not username or len(username) < 3:
        return False, "El usuario debe tener al menos 3 caracteres."
    if len(password) < 4:
        return False, "La contraseña debe tener al menos 4 caracteres."

    users = _load_users()
    if username in users:
        return False, f"El usuario '{username}' ya existe."

    users[username] = {
        "password": _hash_password(password),
        "nombre": nombre.strip() or username.capitalize(),
        "created_at": str(__import__("datetime").datetime.now()),
    }
    _save_users(users)

    # Crear directorio de datos del usuario
    user_dir = DATA_DIR / username
    user_dir.mkdir(exist_ok=True)

    return True, f"Usuario '{username}' creado exitosamente."

def authenticate(username: str, password: str) -> tuple[bool, dict]:
    """
    Authenticate a user.
    Returns (success: bool, user_data: dict).
    """
    username = username.strip().lower()
    users = _load_users()
    user = users.get(username)
    if not user:
        return False, {}
    if _verify_password(password, user["password"]):
        return True, {"username": username, "nombre": user.get("nombre", username.capitalize())}
    return False, {}

def list_users() -> dict:
    """List all users (without passwords)."""
    users = _load_users()
    return {
        u: {"nombre": d.get("nombre", u.capitalize()), "created_at": d.get("created_at", "")}
        for u, d in users.items()
    }

def delete_user(username: str) -> bool:
    """Delete a user and their data directory."""
    username = username.strip().lower()
    users = _load_users()
    if username not in users:
        return False
    del users[username]
    _save_users(users)

    # Remove user data directory
    user_dir = DATA_DIR / username
    if user_dir.exists():
        import shutil
        shutil.rmtree(user_dir)
    return True

def change_password(username: str, old_password: str, new_password: str) -> tuple[bool, str]:
    """Change a user's password."""
    username = username.strip().lower()
    users = _load_users()
    if username not in users:
        return False, "Usuario no encontrado."
    if not _verify_password(old_password, users[username]["password"]):
        return False, "Contraseña actual incorrecta."
    if len(new_password) < 4:
        return False, "La nueva contraseña debe tener al menos 4 caracteres."
    users[username]["password"] = _hash_password(new_password)
    _save_users(users)
    return True, "Contraseña cambiada exitosamente."
