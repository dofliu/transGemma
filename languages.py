"""
Language metadata for TranslateGemma.
"""

# (中文名稱, English name, locale)
LANGUAGES = {
    # East Asian
    "zh_TW": ("繁體中文", "Traditional Chinese", "zh-TW"),
    "zh_CN": ("簡體中文", "Simplified Chinese", "zh-CN"),
    "ja_JP": ("日文", "Japanese", "ja-JP"),
    "ko_KR": ("韓文", "Korean", "ko-KR"),

    # European
    "en_US": ("英文", "English", "en-US"),
    "de_DE": ("德文", "German", "de-DE"),
    "fr_FR": ("法文", "French", "fr-FR"),
    "es_ES": ("西班牙文", "Spanish", "es-ES"),
    "it_IT": ("義大利文", "Italian", "it-IT"),
    "pt_BR": ("葡萄牙文（巴西）", "Portuguese", "pt-BR"),
    "pt_PT": ("葡萄牙文（葡萄牙）", "Portuguese", "pt-PT"),
    "nl_NL": ("荷蘭文", "Dutch", "nl-NL"),
    "pl_PL": ("波蘭文", "Polish", "pl-PL"),
    "ru_RU": ("俄文", "Russian", "ru-RU"),
    "uk_UA": ("烏克蘭文", "Ukrainian", "uk-UA"),
    "cs_CZ": ("捷克文", "Czech", "cs-CZ"),
    "sv_SE": ("瑞典文", "Swedish", "sv-SE"),
    "da_DK": ("丹麥文", "Danish", "da-DK"),
    "fi_FI": ("芬蘭文", "Finnish", "fi-FI"),
    "no_NO": ("挪威文", "Norwegian", "no-NO"),
    "el_GR": ("希臘文", "Greek", "el-GR"),
    "hu_HU": ("匈牙利文", "Hungarian", "hu-HU"),
    "ro_RO": ("羅馬尼亞文", "Romanian", "ro-RO"),
    "sk_SK": ("斯洛伐克文", "Slovak", "sk-SK"),
    "sl_SI": ("斯洛維尼亞文", "Slovenian", "sl-SI"),
    "hr_HR": ("克羅埃西亞文", "Croatian", "hr-HR"),
    "sr_RS": ("塞爾維亞文", "Serbian", "sr-RS"),
    "bg_BG": ("保加利亞文", "Bulgarian", "bg-BG"),
    "lt_LT": ("立陶宛文", "Lithuanian", "lt-LT"),
    "lv_LV": ("拉脫維亞文", "Latvian", "lv-LV"),
    "et_EE": ("愛沙尼亞文", "Estonian", "et-EE"),
    "is_IS": ("冰島文", "Icelandic", "is-IS"),

    # South / Southeast Asian
    "vi_VN": ("越南文", "Vietnamese", "vi-VN"),
    "th_TH": ("泰文", "Thai", "th-TH"),
    "id_ID": ("印尼文", "Indonesian", "id-ID"),
    "ms_MY": ("馬來文", "Malay", "ms-MY"),
    "tl_PH": ("菲律賓文", "Filipino", "fil-PH"),
    "hi_IN": ("印地文", "Hindi", "hi-IN"),
    "bn_IN": ("孟加拉文", "Bengali", "bn-IN"),
    "ta_IN": ("坦米爾文", "Tamil", "ta-IN"),
    "te_IN": ("泰盧固文", "Telugu", "te-IN"),
    "mr_IN": ("馬拉地文", "Marathi", "mr-IN"),
    "gu_IN": ("古吉拉特文", "Gujarati", "gu-IN"),
    "kn_IN": ("卡納達文", "Kannada", "kn-IN"),
    "ml_IN": ("馬拉雅拉姆文", "Malayalam", "ml-IN"),
    "pa_IN": ("旁遮普文", "Punjabi", "pa-IN"),
    "ur_PK": ("烏都文", "Urdu", "ur-PK"),

    # Middle East
    "ar_SA": ("阿拉伯文", "Arabic", "ar-SA"),
    "he_IL": ("希伯來文", "Hebrew", "he-IL"),
    "fa_IR": ("波斯文", "Persian", "fa-IR"),
    "tr_TR": ("土耳其文", "Turkish", "tr-TR"),

    # African
    "sw_KE": ("史瓦希里文（肯亞）", "Swahili", "sw-KE"),
    "sw_TZ": ("史瓦希里文（坦尚尼亞）", "Swahili", "sw-TZ"),
    "zu_ZA": ("祖魯文", "Zulu", "zu-ZA"),
}

# Common languages shown first in dropdown
COMMON_LANGUAGES = [
    "zh_TW", "en_US", "ja_JP", "ko_KR", "zh_CN",
    "de_DE", "fr_FR", "es_ES", "vi_VN", "th_TH",
]


def get_language_choices():
    """Return Gradio dropdown choices with common languages first."""
    choices = []

    for code in COMMON_LANGUAGES:
        if code in LANGUAGES:
            ch_name, en_name, _ = LANGUAGES[code]
            choices.append((f"常用 {ch_name} ({en_name})", code))

    choices.append(("-" * 20, None))

    other_langs = [(code, info) for code, info in LANGUAGES.items() if code not in COMMON_LANGUAGES]
    other_langs.sort(key=lambda x: x[1][0])

    for code, (ch_name, en_name, _) in other_langs:
        choices.append((f"{ch_name} ({en_name})", code))

    return choices


def get_language_info(code: str) -> tuple:
    """Return language metadata by code."""
    return LANGUAGES.get(code, ("Unknown", "Unknown", code))


EDGE_TTS_VOICES = {
    "zh_TW": "zh-TW-HsiaoChenNeural",
    "zh_CN": "zh-CN-XiaoxiaoNeural",
    "en_US": "en-US-JennyNeural",
    "ja_JP": "ja-JP-NanamiNeural",
    "ko_KR": "ko-KR-SunHiNeural",
    "de_DE": "de-DE-KatjaNeural",
    "fr_FR": "fr-FR-DeniseNeural",
    "es_ES": "es-ES-ElviraNeural",
    "it_IT": "it-IT-ElsaNeural",
    "pt_BR": "pt-BR-FranciscaNeural",
    "ru_RU": "ru-RU-SvetlanaNeural",
    "vi_VN": "vi-VN-HoaiMyNeural",
    "th_TH": "th-TH-PremwadeeNeural",
    "id_ID": "id-ID-GadisNeural",
    "ar_SA": "ar-SA-ZariyahNeural",
    "tr_TR": "tr-TR-EmelNeural",
    "pl_PL": "pl-PL-ZofiaNeural",
    "nl_NL": "nl-NL-ColetteNeural",
    "hi_IN": "hi-IN-SwaraNeural",
}


def get_edge_tts_voice(lang_code: str) -> str:
    """Return Edge TTS voice id by language code."""
    return EDGE_TTS_VOICES.get(lang_code, "en-US-JennyNeural")
