"""Constants used throughout the TransX package."""

# File paths and directories
DEFAULT_LOCALES_DIR = "locales"
DEFAULT_MESSAGES_DOMAIN = "messages"

# Locales
DEFAULT_LOCALE = "en_US"
DEFAULT_CHARSET = "utf-8"
DEFAULT_ENCODING = "utf-8"
DEFAULT_LANGUAGES = ["en_US", "zh_CN", "ja_JP", "ko_KR"]

# File formats
PO_FILE_EXTENSION = ".po"
MO_FILE_EXTENSION = ".mo"
POT_FILE_EXTENSION = ".pot"

# Message prefixes in PO files
MSGID_PREFIX = 'msgid "'
MSGSTR_PREFIX = 'msgstr "'
MSGCTXT_PREFIX = 'msgctxt "'

# MO file constants
MO_MAGIC_NUMBER = 0x950412de
MO_VERSION = 0
MO_HEADER_SIZE = 28

# Metadata keys
METADATA_KEYS = {
    "PROJECT_ID_VERSION": "Project-Id-Version",
    "POT_CREATION_DATE": "POT-Creation-Date",
    "PO_REVISION_DATE": "PO-Revision-Date",
    "LAST_TRANSLATOR": "Last-Translator",
    "LANGUAGE_TEAM": "Language-Team",
    "LANGUAGE": "Language",
    "MIME_VERSION": "MIME-Version",
    "CONTENT_TYPE": "Content-Type",
    "CONTENT_TRANSFER_ENCODING": "Content-Transfer-Encoding",
    "GENERATED_BY": "Generated-By",
    "REPORT_MSGID_BUGS_TO": "Report-Msgid-Bugs-To",
    "COPYRIGHT_HOLDER": "Copyright-Holder",
    "COPYRIGHT": "Copyright",
    "PLURAL_FORMS": "Plural-Forms",
}

# MIME settings
MIME_VERSION = "1.0"
MIME_TYPE = "text/plain"
TRANSFER_ENCODING = "8bit"
GENERATOR_NAME = "TransX"
DEFAULT_TRANSLATOR = "FULL NAME <EMAIL@ADDRESS>"
DEFAULT_LANGUAGE_TEAM = "LANGUAGE <LL@li.org>"

# Default metadata values
DEFAULT_METADATA = {
    METADATA_KEYS["PROJECT_ID_VERSION"]: "TransX 1.0",
    METADATA_KEYS["PO_REVISION_DATE"]: "YEAR-MO-DA HO:MI+ZONE",
    METADATA_KEYS["LAST_TRANSLATOR"]: DEFAULT_TRANSLATOR,
    METADATA_KEYS["LANGUAGE_TEAM"]: DEFAULT_LANGUAGE_TEAM,
    METADATA_KEYS["MIME_VERSION"]: MIME_VERSION,
    METADATA_KEYS["CONTENT_TYPE"]: "{0}; charset={1}".format(MIME_TYPE, DEFAULT_CHARSET),
    METADATA_KEYS["CONTENT_TRANSFER_ENCODING"]: TRANSFER_ENCODING,
    METADATA_KEYS["GENERATED_BY"]: GENERATOR_NAME,
}

# Template strings
HEADER_COMMENT = (
    "# Translations template for PROJECT.\n"
    "# Copyright (C) {0} ORGANIZATION\n"
    "# This file is distributed under the same license as the PROJECT project.\n"
    "# FIRST AUTHOR <EMAIL@ADDRESS>, {0}.\n"
    "#\n"
)

# Default values for metadata fields
DEFAULT_PROJECT_VERSION = "PROJECT VERSION"
DEFAULT_BUGS_EMAIL = "EMAIL@ADDRESS"
DEFAULT_LANGUAGE_TEAM_TEMPLATE = "{0} <LL@li.org>"

# Language name mappings
LANGUAGE_NAMES = {
    "en_US": "English (United States)",
    "zh_CN": "Chinese (Simplified)",
    "zh_TW": "Chinese (Traditional)",
    "ja_JP": "Japanese",
    "ko_KR": "Korean",
    "fr_FR": "French",
    "es_ES": "Spanish",
}

# Default metadata for new PO files
DEFAULT_PO_METADATA = {
    METADATA_KEYS["PROJECT_ID_VERSION"]: DEFAULT_PROJECT_VERSION,
    METADATA_KEYS["REPORT_MSGID_BUGS_TO"]: DEFAULT_BUGS_EMAIL,
    METADATA_KEYS["LAST_TRANSLATOR"]: DEFAULT_TRANSLATOR,
    METADATA_KEYS["MIME_VERSION"]: MIME_VERSION,
    METADATA_KEYS["CONTENT_TYPE"]: "{0}; charset={1}".format(MIME_TYPE, DEFAULT_CHARSET),
    METADATA_KEYS["CONTENT_TRANSFER_ENCODING"]: TRANSFER_ENCODING,
    METADATA_KEYS["GENERATED_BY"]: GENERATOR_NAME,
}

# Translation function pattern
# https://regex101.com/r/aAs6bz/1
TR_FUNCTION_PATTERN = r"""tr\((['"])((?:(?!\1|\\).|\\.)*?)\1(?:\s*,\s*context=(['"])((?:(?!\3|\\).|\\.)*?)\3)?[\s,)]*\)"""

# Default keywords for message extraction
DEFAULT_KEYWORDS = {
    "tr": ((1, "c"), 2),  # tr(msgid, context=context)
    "_": None,  # _(msgid)
    "gettext": None,  # gettext(msgid)
    "ngettext": (1, 2),  # ngettext(singular, plural, n)
    "ugettext": None,  # ugettext(msgid)
    "ungettext": (1, 2),  # ungettext(singular, plural, n)
    "dgettext": (2,),  # dgettext(domain, msgid)
    "dngettext": (2, 3),  # dngettext(domain, singular, plural, n)
    "pgettext": ((1, "c"), 2),  # pgettext(context, msgid)
    "npgettext": ((1, "c"), 2, 3),  # npgettext(context, singular, plural, n)
}

# Comment tags and prefixes
TRANSLATOR_COMMENT_PREFIX = "#. "  # Translator comments
EXTRACTED_COMMENT_PREFIX = "#. "  # Extracted comments from source code
REFERENCE_COMMENT_PREFIX = "#: "  # Source file reference comments
FLAG_COMMENT_PREFIX = "#, "  # Special flags (fuzzy, python-format, etc.)

# Default comment tags for source code extraction
DEFAULT_COMMENT_TAGS = [
    "NOTE:",  # General notes for translators
    "TRANSLATORS:",  # Direct messages to translators
    "I18N:",  # Internationalization specific notes
    "CONTEXT:",  # Context information for ambiguous terms
]

# Comment patterns for source code parsing
COMMENT_PATTERNS = {
    "python": [
        r"#\s*({tags})(.+)$",  # Single line comments
        r'"""\s*({tags})(.+?)"""',  # Docstring comments
        r"'''\s*({tags})(.+?)'''",  # Docstring comments
    ],
    "javascript": [
        r"//\s*({tags})(.+)$",  # Single line comments
        r"/\*\s*({tags})(.+?)\*/",  # Multi-line comments
    ],
    "html": [
        r"<!--\s*({tags})(.+?)-->",  # HTML comments
    ],
}

# Regular expression for extracting comments
COMMENT_REGEX = r"(?P<tag>{tags})\s*(?P<text>.+)"

# Language codes and mappings
LANGUAGE_CODES = {
    # East Asian Languages
    "zh_CN": ("Chinese (Simplified)", ["zh-CN", "zh_cn", "zh-cn", "zhs", "cn", "chi"]),
    "zh_TW": ("Chinese (Traditional)", ["zh-TW", "zh_tw", "zh-tw", "zht", "tw"]),
    "ja_JP": ("Japanese", ["ja", "ja-JP", "jp", "jpn"]),
    "ko_KR": ("Korean", ["ko", "ko-KR", "kr", "kor"]),

    # European Languages
    "en_US": ("English (US)", ["en", "en-US", "eng", "us"]),
    "fr_FR": ("French", ["fr", "fr-FR", "fra", "fre"]),
    "de_DE": ("German", ["de", "de-DE", "deu", "ger"]),
    "es_ES": ("Spanish", ["es", "es-ES", "spa"]),
    "it_IT": ("Italian", ["it", "it-IT", "ita"]),
    "ru_RU": ("Russian", ["ru", "ru-RU", "rus"]),
}

# Common language code mappings
LANGUAGE_MAP = {
    "zh_hans": "zh_CN",
    "zh_chs": "zh_CN",
    "zh_hant": "zh_TW",
    "zh_cht": "zh_TW",
    "chinese_simplified": "zh_CN",
    "chinese_traditional": "zh_TW",
    "chinese": "zh_CN",
    "japanese": "ja_JP",
    "korean": "ko_KR",
    "french": "fr_FR",
    "spanish": "es_ES",
    "english": "en_US",
}

# Default country code for language codes
DEFAULT_COUNTRY_MAP = {
    "zh": "CN",
    "ja": "JP",
    "ko": "KR",
    "en": "US",
    "fr": "FR",
    "es": "ES",
    "de": "DE",
    "it": "IT",
    "ru": "RU",
}

# Mapping of non-standard codes to standard codes
LANGUAGE_CODE_ALIASES = {
    alias.lower(): code
    for code, (name, aliases) in LANGUAGE_CODES.items()
    for alias in aliases
}

# Error messages
INVALID_LANGUAGE_CODE_ERROR = """
Invalid language code: "{code}"

Valid language codes are:
{valid_codes}

For more information about language codes, visit:
- ISO 639-1: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
- ISO 3166-1: https://en.wikipedia.org/wiki/ISO_3166-1
"""

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Mobile Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "*",
    "Connection": "keep-alive"
}
