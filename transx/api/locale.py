from transx.constants import DEFAULT_LOCALE
from transx.constants import INVALID_LANGUAGE_CODE_ERROR
from transx.constants import LANGUAGE_CODES
from transx.constants import LANGUAGE_CODE_ALIASES

def normalize_locale(locale):
    """Normalize language code format.

    Convert various language code formats to standard format (e.g., 'zh-CN' -> 'zh_CN').
    Supported formats include:
    - ISO 639-1 language codes (e.g., 'en')
    - ISO 3166-1 country/region codes (e.g., 'zh_CN')
    - Common non-standard codes (e.g., 'cn' -> 'zh_CN')

    Args:
        locale (str): Language code (e.g., 'zh-CN', 'zh_cn', 'zh')

    Returns:
        str: Normalized language code (e.g., 'zh_CN')

    Raises:
        ValueError: If an invalid language code is provided

    """
    if not locale:
        return DEFAULT_LOCALE

    # Remove all whitespace and convert to lowercase
    normalized = locale.strip().lower()

    # Check if it's a standard code
    if normalized in LANGUAGE_CODES:
        return normalized

    # Check if it's an alias
    if normalized in LANGUAGE_CODE_ALIASES:
        return LANGUAGE_CODE_ALIASES[normalized]

    # If the code contains a separator, try to normalize the format
    if "-" in normalized or "_" in normalized:
        parts = normalized.replace("-", "_").split("_")
        if len(parts) == 2:
            lang, region = parts
            # Build a possible standard code
            possible_code = f"{lang}_{region.upper()}"
            if possible_code in LANGUAGE_CODES:
                return possible_code

    # If no matching code is found, generate an error message
    valid_codes = "\n".join(
        "- {} ({}): {}".format(
            code,
            name,
            ", ".join(["'" + a + "'" for a in aliases])
        )
        for code, (name, aliases) in sorted(LANGUAGE_CODES.items())
    )

    raise ValueError(
        INVALID_LANGUAGE_CODE_ERROR.format(
            code=locale,
            valid_codes=valid_codes
        )
    )