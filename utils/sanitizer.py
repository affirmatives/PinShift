from __future__ import annotations

import re


_SENSITIVE_QUERY_PATTERNS = (
    re.compile(r"([?&](?:key|securityJsCode)=)[^&\s#]+", re.IGNORECASE),
    re.compile(r"((?:key|securityJsCode)\s*[:=]\s*)['\"]?[^,'\"\s&}]+", re.IGNORECASE),
)


def sanitize_log_text(message: object) -> str:
    text = str(message)
    for pattern in _SENSITIVE_QUERY_PATTERNS:
        text = pattern.sub(r"\1***", text)
    return text
