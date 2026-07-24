"""
utils/validator.py — Sanitização e validação de input.
"""
import re, unicodedata

MAX_LEN  = 512
MAX_WORD = 128
_INJ = [
    (r";\s*(rm|mkfs|dd|shutdown|poweroff|halt)\b", "injecao destrutiva"),
    (r"\|\s*bash\b",   "pipe para bash bloqueado"),
    (r"\|\s*sh\b",     "pipe para sh bloqueado"),
    (r">\s*/etc/passwd","escrita em /etc/passwd"),
    (r">\s*/dev/[shn]d","escrita em dispositivo"),
]
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\x80-\x9f]")

class ValidationResult:
    __slots__ = ("ok","value","reason")
    def __init__(self, ok, value, reason=""):
        self.ok=ok; self.value=value; self.reason=reason
    def __iter__(self): return iter((self.ok, self.value, self.reason))
    def __bool__(self): return self.ok

class Validator:
    @staticmethod
    def validate(raw):
        if not isinstance(raw, str):
            return ValidationResult(False,"","deve ser string")
        if len(raw) > MAX_LEN:
            return ValidationResult(False,"",f"muito longo ({len(raw)} chars, max {MAX_LEN})")
        for w in raw.split():
            if len(w) > MAX_WORD:
                return ValidationResult(False,"","palavra muito longa")
        if _CTRL.search(raw):
            return ValidationResult(False,"","caracteres de controlo")
        for pat, reason in _INJ:
            if re.search(pat, raw, re.IGNORECASE):
                return ValidationResult(False,"",f"bloqueado: {reason}")
        return ValidationResult(True, Validator.sanitize(raw))

    @staticmethod
    def sanitize(raw):
        n = unicodedata.normalize("NFKC", raw)
        c = _CTRL.sub("", n)
        return " ".join(c.split())

    @staticmethod
    def is_empty(t): return not t or not t.strip()
