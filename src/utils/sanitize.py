import re

from src.database.models import Role, UserStatus

_SUSPICIOUS = re.compile(
    r"(ignore (all |any )?previous|system:|developer:|you are now|jailbreak)",
    re.IGNORECASE,
)

_ROLE_NAMES = {role.value for role in Role}
_STATUS_NAMES = {status.value for status in UserStatus}


def sanitize_prompt(prompt: str) -> str:
    """Удаляет подозрительные конструкции перед отправкой в LLM."""
    return _SUSPICIOUS.sub("", prompt).strip()


def parse_role(value: str) -> Role | None:
    value = value.strip().lower()
    for role in Role:
        if role.value == value:
            return role
    return None


def parse_user_target(value: str) -> tuple[str, int | str] | None:
    """Возвращает ('id', int) для числового ID или ('username', str) для @ник."""
    value = value.strip()
    if re.fullmatch(r"\d{5,16}", value):
        return ("id", int(value))
    if re.fullmatch(r"@[\w_]{5,32}", value):
        return ("username", value[1:].lower())
    return None


def is_role(value: str) -> bool:
    return value.strip().lower() in _ROLE_NAMES


def is_status(value: str) -> bool:
    return value.strip().lower() in _STATUS_NAMES
