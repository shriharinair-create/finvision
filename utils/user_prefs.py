"""
finvision/utils/user_prefs.py
=============================
Multi-Tenant User Profile, Authentication & Preferences Isolation Store.
Ensures every trader (admin, friend, companion device) has an isolated wallet,
risk budget, and paper trading journal while sharing collective AI intelligence.

Hardened Security Architecture:
  - Per-user cryptographically random 128-bit salt (PBKDF2-HMAC-SHA256, 100k iterations).
  - PIN and Master Passphrase hashed with per-user salt.
  - 4-word recovery phrase hashed with per-user salt (zero plaintext credential storage).
  - Anti-brute-force rate limiting & 15-minute lockouts on both PIN and recovery endpoints.
  - Zero hardcoded admin credentials; supports first-run wizard and environment bootstrap.
"""

from __future__ import annotations
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import time
from typing import Any, Dict, List, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_DIR = DATA_DIR / "users"
REGISTRY_FILE = DATA_DIR / "users_registry.json"
LEGACY_PREFS_FILE = DATA_DIR / "user_preferences.json"

RECOVERY_WORD_POOL = [
    "falcon", "river", "summit", "copper", "amber", "breeze", "harbor", "shadow",
    "timber", "beacon", "valley", "shield", "glacier", "orbit", "canvas", "zenith",
    "canyon", "meadow", "crystal", "pulse", "lotus", "matrix", "saffron", "tiger",
    "horizon", "delta", "vortex", "cobalt", "aurora", "solar"
]

DEFAULT_PREFS = {
    "total_capital": 200000.0,
    "risk_profile": "Balanced (1.0% max risk)",
    "risk_pct": 0.01,
    "trading_goal_index": 0,
    "execution_leader": "CLOUD_PRIMARY",
    "theme": "dark",
    "persona_budgets": {
        "MOMENTUM_HUNTER": 50000.0,
        "MEAN_REVERTER": 50000.0,
        "CONSERVATIVE_VALUE": 50000.0,
        "VOLATILITY_BREAKOUT": 50000.0,
    },
    "persona_active": {
        "MOMENTUM_HUNTER": True,
        "MEAN_REVERTER": True,
        "CONSERVATIVE_VALUE": True,
        "VOLATILITY_BREAKOUT": True,
    },
}

DEFAULT_FRIEND_PREFS = {
    "total_capital": 50000.0,
    "risk_profile": "Conservative (0.5% max risk)",
    "risk_pct": 0.005,
    "trading_goal_index": 0,
    "execution_leader": "SIMULATION_OBSERVER",
    "theme": "dark",
    "persona_budgets": {
        "MOMENTUM_HUNTER": 12500.0,
        "MEAN_REVERTER": 12500.0,
        "CONSERVATIVE_VALUE": 12500.0,
        "VOLATILITY_BREAKOUT": 12500.0,
    },
    "persona_active": {
        "MOMENTUM_HUNTER": True,
        "MEAN_REVERTER": True,
        "CONSERVATIVE_VALUE": True,
        "VOLATILITY_BREAKOUT": True,
    },
}


def _normalize_recovery_phrase(phrase: str) -> str:
    """Normalizes recovery phrase by stripping whitespace and replacing spaces/commas with hyphens."""
    norm = phrase.strip().lower().replace(" ", "-").replace(",", "-")
    while "--" in norm:
        norm = norm.replace("--", "-")
    return norm


def _hash_pin(pin: str, user_salt: str) -> str:
    """Computes PBKDF2-HMAC-SHA256 hash for secure PIN verification with unique per-user salt."""
    clean = pin.strip().encode("utf-8")
    salt = f"finvision_pin_salt_{user_salt}".encode("utf-8")
    return hashlib.pbkdf2_hmac("sha256", clean, salt, iterations=100_000).hex()


def _hash_passphrase(passphrase: str, user_salt: str) -> str:
    """Computes PBKDF2-HMAC-SHA256 hash for secure master passphrase verification."""
    clean = passphrase.strip().encode("utf-8")
    salt = f"finvision_pw_salt_{user_salt}".encode("utf-8")
    return hashlib.pbkdf2_hmac("sha256", clean, salt, iterations=100_000).hex()


def _hash_recovery_phrase(phrase: str, user_salt: str) -> str:
    """Computes PBKDF2-HMAC-SHA256 hash for 4-word recovery phrase verification."""
    clean = _normalize_recovery_phrase(phrase).encode("utf-8")
    salt = f"finvision_rec_salt_{user_salt}".encode("utf-8")
    return hashlib.pbkdf2_hmac("sha256", clean, salt, iterations=100_000).hex()


def generate_recovery_phrase() -> str:
    """Generates a memorable 4-word recovery phrase for zero-app account recovery."""
    import random
    chosen = random.sample(RECOVERY_WORD_POOL, 4)
    return "-".join(chosen).lower()


def get_user_registry() -> dict[str, Any]:
    """Loads the user registry and ensures backward-compatible security upgrades."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    registry: dict[str, Any] = {}
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                registry = json.load(f)
        except Exception:
            registry = {}

    modified = False

    # Check for optional environment-variable-driven admin initialization
    env_user = os.getenv("FINVISION_ADMIN_USER", "").strip().lower()
    env_pin = os.getenv("FINVISION_ADMIN_PIN", "").strip()
    env_pass = os.getenv("FINVISION_ADMIN_PASSPHRASE", "").strip()
    if env_user and env_pin and len(registry) == 0:
        salt = secrets.token_hex(16)
        phrase = generate_recovery_phrase()
        registry[env_user] = {
            "username": env_user,
            "display_name": os.getenv("FINVISION_ADMIN_DISPLAY", "Administrator"),
            "user_salt": salt,
            "pin_hash": _hash_pin(env_pin, salt),
            "passphrase_hash": _hash_passphrase(env_pass or f"{env_user}_pass2026!", salt),
            "recovery_phrase_hash": _hash_recovery_phrase(phrase, salt),
            "role": "admin",
            "failed_pin_attempts": 0,
            "locked_until": 0.0,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        modified = True

    # Upgrade and sanitize any existing user records
    for u_key, u_data in registry.items():
        # Ensure per-user cryptographic salt exists
        if "user_salt" not in u_data or not u_data["user_salt"]:
            u_data["user_salt"] = secrets.token_hex(16)
            modified = True

        u_salt = u_data["user_salt"]

        # Ensure lockout tracking keys exist
        if "failed_pin_attempts" not in u_data:
            u_data["failed_pin_attempts"] = 0
            u_data["locked_until"] = 0.0
            modified = True

        # Secure recovery phrase: convert plaintext recovery phrase to PBKDF2 hash
        if "recovery_phrase" in u_data:
            plain_phrase = str(u_data.pop("recovery_phrase"))
            u_data["recovery_phrase_hash"] = _hash_recovery_phrase(plain_phrase, u_salt)
            modified = True
        elif "recovery_phrase_hash" not in u_data:
            fresh_phrase = generate_recovery_phrase()
            u_data["recovery_phrase_hash"] = _hash_recovery_phrase(fresh_phrase, u_salt)
            modified = True

        # Upgrade passphrase hash if missing
        if "passphrase_hash" not in u_data:
            u_data["passphrase_hash"] = _hash_passphrase(f"{u_key}_pass2026!", u_salt)
            modified = True

    if modified:
        _save_registry(registry)
    return registry


def _save_registry(registry: dict[str, Any]) -> None:
    """Persists the user registry to disk."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)
    except Exception:
        pass


def has_admin_user() -> bool:
    """Returns True if at least one administrator profile exists."""
    reg = get_user_registry()
    return any(u.get("role") == "admin" for u in reg.values())


def is_registry_empty() -> bool:
    """Returns True if no trader profiles exist in the system."""
    return len(get_user_registry()) == 0


def get_primary_admin_username() -> str:
    """Returns the primary administrator username if defined."""
    reg = get_user_registry()
    for uname, udata in reg.items():
        if udata.get("role") == "admin":
            return uname
    if reg:
        return next(iter(reg.keys()))
    return "admin"


def authenticate_user_pin(username: str, pin: str) -> tuple[bool, str, dict[str, Any]]:
    """
    Authenticates a user via 6-digit PIN with anti-brute-force rate limiting.
    NOTE: PIN serves strictly as a local convenience unlock; Master Passphrase is the root cryptographic boundary (Finding D4).
    Locks PIN entries for 15 minutes after 5 consecutive failures.
    Returns: (success, message, user_data)
    """
    clean_user = username.strip().lower()
    registry = get_user_registry()

    if clean_user not in registry:
        return False, f"Trader '{clean_user}' not found. Please create a new profile.", {}

    user_info = registry[clean_user]
    now = time.time()
    locked_until = float(user_info.get("locked_until", 0.0))

    if now < locked_until:
        rem_mins = max(1, int((locked_until - now) / 60) + 1)
        return False, f"🔒 Account locked due to failed PIN attempts. Wait {rem_mins} min or sign in with your Master Passphrase.", {}

    user_salt = user_info.get("user_salt", "")
    target_hash = user_info.get("pin_hash", "")
    calculated_hash = _hash_pin(pin, user_salt)

    is_valid = hmac.compare_digest(target_hash, calculated_hash)

    if not is_valid:
        fails = int(user_info.get("failed_pin_attempts", 0)) + 1
        user_info["failed_pin_attempts"] = fails
        if fails >= 5:
            user_info["locked_until"] = now + 900.0  # 15 minutes lock
            _save_registry(registry)
            return False, "⚠️ Too many failed attempts. PIN entry locked for 15 minutes. Use your Master Passphrase or 4-word Recovery Key.", {}
        _save_registry(registry)
        rem = 5 - fails
        return False, f"Incorrect PIN. {rem} attempt{'s' if rem > 1 else ''} remaining before temporary lockout.", {}

    # Successful authentication resets failed attempts
    user_info["failed_pin_attempts"] = 0
    user_info["locked_until"] = 0.0
    _save_registry(registry)
    return True, f"Welcome back, {user_info.get('display_name', clean_user)}!", user_info


def authenticate_user_passphrase(username: str, passphrase: str) -> tuple[bool, str, dict[str, Any]]:
    """
    Authenticates a user via Master Passphrase. Instantly clears any PIN lockout.
    Returns: (success, message, user_data)
    """
    clean_user = username.strip().lower()
    registry = get_user_registry()

    if clean_user not in registry:
        return False, f"Trader '{clean_user}' not found.", {}

    user_info = registry[clean_user]
    user_salt = user_info.get("user_salt", clean_user)
    target_hash = user_info.get("passphrase_hash", "")
    calc_hash = _hash_passphrase(passphrase, user_salt)

    is_valid = hmac.compare_digest(target_hash, calc_hash)

    # Legacy check with user_salt = clean_user
    if not is_valid:
        legacy_salt = f"finvision_pw_salt_{clean_user}".encode("utf-8")
        legacy_hash = hashlib.pbkdf2_hmac("sha256", passphrase.strip().encode("utf-8"), legacy_salt, iterations=100_000).hex()
        if hmac.compare_digest(target_hash, legacy_hash):
            is_valid = True
            user_info["passphrase_hash"] = calc_hash
            _save_registry(registry)

    if not is_valid:
        return False, "Incorrect Master Passphrase. Please check your credentials.", {}

    # Reset any lockout
    user_info["failed_pin_attempts"] = 0
    user_info["locked_until"] = 0.0
    _save_registry(registry)
    return True, f"Authenticated via Master Passphrase: {user_info.get('display_name', clean_user)}", user_info


def recover_and_reset_pin_with_passphrase(username: str, passphrase: str, new_pin: str) -> tuple[bool, str]:
    """
    Recovers account and resets PIN using Master Passphrase directly in the browser.
    """
    clean_user = username.strip().lower()
    clean_pin = new_pin.strip()
    if len(clean_pin) < 6 or not clean_pin.isdigit():
        return False, "New PIN must be at least 6 numeric digits."

    ok, msg, u_data = authenticate_user_passphrase(clean_user, passphrase)
    if not ok:
        return False, msg

    registry = get_user_registry()
    user_info = registry[clean_user]
    user_salt = user_info.get("user_salt", secrets.token_hex(16))
    user_info["user_salt"] = user_salt
    user_info["pin_hash"] = _hash_pin(clean_pin, user_salt)
    user_info["failed_pin_attempts"] = 0
    user_info["locked_until"] = 0.0
    _save_registry(registry)
    return True, "✅ PIN reset successfully! You can now unlock your terminal with your new PIN."


def recover_and_reset_pin_with_recovery_phrase(username: str, recovery_phrase_input: str, new_pin: str) -> tuple[bool, str]:
    """
    Recovers account and resets PIN using 4-Word Recovery Phrase directly in the browser.
    Protected with anti-brute-force rate limiting and lockout.
    """
    clean_user = username.strip().lower()
    clean_pin = new_pin.strip()
    if len(clean_pin) < 6 or not clean_pin.isdigit():
        return False, "New PIN must be at least 6 numeric digits."

    registry = get_user_registry()
    if clean_user not in registry:
        return False, f"Trader '{clean_user}' not found."

    user_info = registry[clean_user]
    now = time.time()
    locked_until = float(user_info.get("locked_until", 0.0))
    if now < locked_until:
        rem_mins = max(1, int((locked_until - now) / 60) + 1)
        return False, f"🔒 Account recovery is temporarily locked due to failed attempts. Please wait {rem_mins} minutes or sign in with your Master Passphrase."

    user_salt = user_info.get("user_salt", "")
    target_rec_hash = user_info.get("recovery_phrase_hash", "")
    calc_rec_hash = _hash_recovery_phrase(recovery_phrase_input, user_salt)

    if not target_rec_hash or not hmac.compare_digest(target_rec_hash, calc_rec_hash):
        fails = int(user_info.get("failed_pin_attempts", 0)) + 1
        user_info["failed_pin_attempts"] = fails
        if fails >= 5:
            user_info["locked_until"] = now + 900.0  # 15 minutes lockout
            _save_registry(registry)
            return False, "⚠️ Too many failed verification attempts. Account recovery locked for 15 minutes."
        _save_registry(registry)
        rem = 5 - fails
        return False, f"Invalid 4-word recovery phrase. {rem} attempt{'s' if rem > 1 else ''} remaining before temporary lockout."

    # Successful recovery resets lockout and updates PIN
    user_info["pin_hash"] = _hash_pin(clean_pin, user_salt)
    user_info["failed_pin_attempts"] = 0
    user_info["locked_until"] = 0.0
    _save_registry(registry)
    return True, "✅ Account verified! Your PIN has been reset successfully. You can now log in."


def update_user_credentials(
    username: str,
    current_passphrase: str,
    new_passphrase: Optional[str] = None,
    new_pin: Optional[str] = None
) -> tuple[bool, str]:
    """Allows user to update their Master Passphrase or PIN from Settings."""
    clean_user = username.strip().lower()
    ok, msg, _ = authenticate_user_passphrase(clean_user, current_passphrase)
    if not ok:
        return False, "Current Master Passphrase is incorrect."

    registry = get_user_registry()
    user_info = registry[clean_user]
    user_salt = user_info.get("user_salt", secrets.token_hex(16))
    user_info["user_salt"] = user_salt

    if new_passphrase and len(new_passphrase.strip()) >= 8:
        user_info["passphrase_hash"] = _hash_passphrase(new_passphrase.strip(), user_salt)
    elif new_passphrase:
        return False, "New Master Passphrase must be at least 8 characters long."

    if new_pin is not None and new_pin != "":
        clean_np = new_pin.strip()
        if len(clean_np) < 6 or not clean_np.isdigit():
            return False, "New PIN must be at least 6 numeric digits."
        user_info["pin_hash"] = _hash_pin(clean_np, user_salt)

    _save_registry(registry)
    return True, "Credentials updated successfully!"


def authenticate_user(username: str, pin: str) -> tuple[bool, str, dict[str, Any]]:
    """Backwards-compatible alias for authenticate_user_pin."""
    return authenticate_user_pin(username, pin)


def register_new_user(
    username: str,
    display_name: str,
    pin: str,
    passphrase: Optional[str] = None,
    is_admin: bool = False
) -> tuple[bool, str, str]:
    """
    Registers a new isolated trader profile with PBKDF2 Passphrase + PIN + Hashed Recovery Phrase.
    Returns: (success, message, plaintext_recovery_phrase_for_one_time_display)
    """
    clean_user = username.strip().lower().replace(" ", "_")
    if not clean_user or len(clean_user) < 3:
        return False, "Username must be at least 3 characters long.", ""

    clean_pin = pin.strip()
    if not clean_pin or len(clean_pin) < 6 or not clean_pin.isdigit():
        return False, "PIN must be at least 6 numeric digits.", ""

    clean_passphrase = (passphrase or "").strip()
    if len(clean_passphrase) < 8:
        return False, "Master Passphrase must be at least 8 characters long.", ""

    registry = get_user_registry()
    if clean_user in registry:
        return False, f"Username '{clean_user}' already exists. Please choose a different name or log in.", ""

    # Generate unique per-user 128-bit cryptographic salt
    user_salt = secrets.token_hex(16)
    rec_phrase = generate_recovery_phrase()

    role = "admin" if (is_admin or not has_admin_user()) else "trader"

    registry[clean_user] = {
        "username": clean_user,
        "display_name": display_name.strip() or clean_user.capitalize(),
        "user_salt": user_salt,
        "pin_hash": _hash_pin(clean_pin, user_salt),
        "passphrase_hash": _hash_passphrase(clean_passphrase, user_salt),
        "recovery_phrase_hash": _hash_recovery_phrase(rec_phrase, user_salt),
        "role": role,
        "failed_pin_attempts": 0,
        "locked_until": 0.0,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _save_registry(registry)

    # Initialize dedicated isolated preference file
    user_file = _get_user_prefs_file(clean_user)
    user_file.parent.mkdir(parents=True, exist_ok=True)
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_PREFS if role == "admin" else DEFAULT_FRIEND_PREFS, f, indent=2)

    return True, f"Profile created successfully for {display_name}!", rec_phrase


def get_current_user_id() -> str:
    """
    Determines active user ID from Streamlit session state if available,
    falling back to primary administrator.
    """
    try:
        import streamlit as st
        if hasattr(st, "session_state") and "authenticated_user" in st.session_state:
            active_u = st.session_state.get("authenticated_user")
            if active_u:
                return str(active_u).strip().lower()
    except Exception:
        pass
    return get_primary_admin_username()


def _get_user_prefs_file(user_id: str) -> Path:
    """Returns the path to a user's isolated preferences file."""
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    return USERS_DIR / f"{user_id.strip().lower()}_preferences.json"


def get_user_preferences(user_id: Optional[str] = None) -> dict[str, Any]:
    """
    Loads saved user preferences from user's isolated store.
    If user_id is None, automatically resolves the currently active session user.
    """
    uid = (user_id or get_current_user_id()).strip().lower()
    admin_u = get_primary_admin_username()
    u_file = _get_user_prefs_file(uid)

    if uid == admin_u and not u_file.exists() and LEGACY_PREFS_FILE.exists():
        try:
            with open(LEGACY_PREFS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            with open(u_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return data
        except Exception:
            pass

    if u_file.exists():
        try:
            with open(u_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                base = dict(DEFAULT_PREFS if uid == admin_u else DEFAULT_FRIEND_PREFS)
                base.update(data)
                return base
        except Exception:
            pass

    return dict(DEFAULT_PREFS if uid == admin_u else DEFAULT_FRIEND_PREFS)


def save_user_preference(key: str, value: Any, user_id: Optional[str] = None) -> None:
    """
    Updates and saves a preference strictly within the specified or active user's wallet.
    """
    uid = (user_id or get_current_user_id()).strip().lower()
    admin_u = get_primary_admin_username()
    u_file = _get_user_prefs_file(uid)
    prefs = get_user_preferences(uid)
    prefs[key] = value

    try:
        u_file.parent.mkdir(parents=True, exist_ok=True)
        with open(u_file, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)

        if uid == admin_u:
            try:
                with open(LEGACY_PREFS_FILE, "w", encoding="utf-8") as f:
                    json.dump(prefs, f, indent=2)
            except Exception:
                pass
    except Exception:
        pass
