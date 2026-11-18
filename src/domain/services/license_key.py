import uuid

from src.domain.rules import LICENSE_KEY_PREFIX


def generate_license_key() -> str:
    """Генерирует ключ лицензии: `drl_` + UUID4 в виде 32 hex-символов"""
    return f"{LICENSE_KEY_PREFIX}{uuid.uuid4().hex}"
