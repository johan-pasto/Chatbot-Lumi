# core/crypto.py — Encriptación del historial_chat

from cryptography.fernet import Fernet
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def _get_fernet() -> Fernet:
    """
    Obtiene o genera la clave Fernet.
    En producción, usa una variable de entorno: LUMI_ENCRYPTION_KEY
    """
    key = os.environ.get("LUMI_ENCRYPTION_KEY")
    
    if not key:
        # Modo desarrollo: genera una clave si no existe (NO uses esto en producción)
        # La clave se guarda en un archivo para persistencia entre reinicios
        key_path = ".lumi_secret.key"
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                key = f.read().decode()
        else:
            # Generar clave nueva
            password = b"lumi_default_dev_password_2026"  # Cambia esto en prod
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password)).decode()
            with open(key_path, "wb") as f:
                f.write(key.encode())
            # Guardar salt también
            with open(".lumi_salt.bin", "wb") as f:
                f.write(salt)
    
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_message(texto: str) -> str:
    """Encripta un mensaje y devuelve string base64."""
    f = _get_fernet()
    return f.encrypt(texto.encode("utf-8")).decode("utf-8")


def decrypt_message(token: str) -> str:
    """Desencripta un token base64 y devuelve el texto original."""
    f = _get_fernet()
    return f.decrypt(token.encode("utf-8")).decode("utf-8")


def encrypt_chat_history(historial: list[dict]) -> list[dict]:
    """
    Encripta el campo 'texto' de cada mensaje en el historial.
    Mantiene el resto de metadatos (rol, timestamp) en claro.
    """
    historial_encriptado = []
    for msg in historial:
        msg_copy = msg.copy()
        if "texto" in msg_copy and msg_copy["texto"]:
            msg_copy["texto"] = encrypt_message(msg_copy["texto"])
        historial_encriptado.append(msg_copy)
    return historial_encriptado


def decrypt_chat_history(historial: list[dict]) -> list[dict]:
    """
    Desencripta el campo 'texto' de cada mensaje en el historial.
    """
    historial_desencriptado = []
    for msg in historial:
        msg_copy = msg.copy()
        if "texto" in msg_copy and msg_copy["texto"]:
            try:
                msg_copy["texto"] = decrypt_message(msg_copy["texto"])
            except Exception as e:
                # Si falla la desencriptación, marca como corrupto pero no crashea
                msg_copy["texto"] = f"[🔒 Mensaje encriptado ilegible: {str(e)}]"
        historial_desencriptado.append(msg_copy)
    return historial_desencriptado