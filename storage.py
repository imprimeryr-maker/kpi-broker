"""
storage.py - Almacenamiento JSON por usuario
- Carga Diaria (daily data entries)
- Config Metas (goals)
- Dashboard data (computed metrics)
"""

import json
import warnings
import shutil
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")

def _get_user_dir(username: str) -> Path:
    """Get the data directory for a specific user."""
    return DATA_DIR / username.strip().lower()

def _ensure_user_dir(username: str):
    """Ensure user directory exists."""
    user_dir = _get_user_dir(username)
    user_dir.mkdir(parents=True, exist_ok=True)

# ─── Config Metas (Goals) ─────────────────────────────────────────────

def get_default_metas() -> dict:
    """Return default goals configuration."""
    return {
        "tasa_contacto": 0.50,        # 50%
        "tasa_agendamiento": 0.15,    # 15%
        "tasa_show": 0.10,            # 10%
        "tasa_reserva": 0.70,         # 70%
        "tasa_cierre": 0.70,          # 70%
        "uf_vendidas_semana": 3750.0, # UF
        "cobertura_llamados": 1.00,   # 100%
        "uf_promedio_venta": 3500.0,  # UF
        "precio_uf": 24000.0,         # CLP
        "meta_diaria_leads": 0,       # 0 = dinámico
        "meta_reuniones_agendadas": 5,   # reuniones agendadas por día
        "meta_reuniones_efectuadas": 3,  # reuniones efectuadas por día
    }

def _backup_corrupted(path: Path):
    """Backup a corrupted file before data loss."""
    if path.exists():
        backup = path.with_suffix(".json.bak")
        try:
                shutil.copy2(path, backup)
        except Exception:
            pass

def load_metas(username: str) -> dict:
    """Load goals config for a user, or return defaults."""
    _ensure_user_dir(username)
    path = _get_user_dir(username) / "config_metas.json"
    if path.exists():
        try:
            with open(path, "r") as f:
                data = json.load(f)
            # Merge with defaults to ensure all keys exist
            defaults = get_default_metas()
            defaults.update(data)
            return defaults
        except (json.JSONDecodeError, Exception):
            _backup_corrupted(path)
            print(f"⚠️ El archivo de metas para '{username}' está dañado. Se usaron valores por defecto. Backup: {path}.bak")
            return get_default_metas()
    return get_default_metas()

def save_metas(username: str, metas: dict):
    """Save goals config for a user."""
    _ensure_user_dir(username)
    path = _get_user_dir(username) / "config_metas.json"
    with open(path, "w") as f:
        json.dump(metas, f, indent=2)

# ─── Carga Diaria (Daily Data) ────────────────────────────────────────

def get_default_entry(fecha: str = None) -> dict:
    """Return a default daily entry structure."""
    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")
    return {
        "fecha": fecha,
        "semana": "",
        "dia": "",
        "leads_nuevos": 0,
        "llamadas": 0,
        "contactos": 0,
        "tasa_contacto": 0.0,
        "agendas": 0,
        "tasa_agendamiento": 0.0,
        "reuniones": 0,
        "tasa_show": 0.0,
        "reservas": 0,
        "tasa_reserva": 0.0,
        "ventas": 0,
        "tasa_cierre": 0.0,
        "uf_vendidas": 0.0,
        "ingreso_bruto": 0.0,
        "diagnostico": "",
        "observaciones": "",
        "accion_correctiva": "",
    }

def load_carga_diaria(username: str) -> list:
    """Load all daily entries for a user."""
    _ensure_user_dir(username)
    path = _get_user_dir(username) / "carga_diaria.json"
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            _backup_corrupted(path)
            print(f"⚠️ El archivo de datos para '{username}' está dañado. Se usaron datos vacíos. Backup: {path}.bak")
            return []
    return []

def save_carga_diaria(username: str, entries: list):
    """Save all daily entries for a user."""
    _ensure_user_dir(username)
    path = _get_user_dir(username) / "carga_diaria.json"
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)

def add_entry(username: str, entry: dict):
    """Add a new daily entry (or update if same date exists)."""
    entries = load_carga_diaria(username)
    # Check if entry for this date already exists
    fecha = entry.get("fecha", "")
    for i, e in enumerate(entries):
        if e.get("fecha") == fecha:
            entries[i] = entry
            save_carga_diaria(username, entries)
            return "editada"
    entries.append(entry)
    # Sort by date
    entries.sort(key=lambda x: x.get("fecha", ""))
    save_carga_diaria(username, entries)
    return "creada"

def delete_entry(username: str, fecha: str) -> bool:
    """Delete an entry by date."""
    entries = load_carga_diaria(username)
    new_entries = [e for e in entries if e.get("fecha") != fecha]
    if len(new_entries) == len(entries):
        return False
    save_carga_diaria(username, new_entries)
    return True

def get_entry_by_date(username: str, fecha: str) -> dict | None:
    """Get a single entry by date."""
    entries = load_carga_diaria(username)
    for e in entries:
        if e.get("fecha") == fecha:
            return e
    return None
