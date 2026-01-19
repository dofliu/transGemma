"""
TranslateGemma 語言對照表
==========================
支援 55 種語言的名稱、英文名稱和語言代碼
"""

# 語言清單 (中文名稱, 英文名稱, 語言代碼)
LANGUAGES = {
    # 東亞語言
    "zh_TW": ("繁體中文", "Traditional Chinese", "zh-TW"),
    "zh_CN": ("簡體中文", "Simplified Chinese", "zh-CN"),
    "ja_JP": ("日文", "Japanese", "ja-JP"),
    "ko_KR": ("韓文", "Korean", "ko-KR"),
    
    # 歐洲語言
    "en_US": ("英文", "English", "en-US"),
    "de_DE": ("德文", "German", "de-DE"),
    "fr_FR": ("法文", "French", "fr-FR"),
    "es_ES": ("西班牙文", "Spanish", "es-ES"),
    "it_IT": ("義大利文", "Italian", "it-IT"),
    "pt_BR": ("葡萄牙文(巴西)", "Portuguese", "pt-BR"),
    "pt_PT": ("葡萄牙文(葡萄牙)", "Portuguese", "pt-PT"),
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
    
    # 亞洲語言
    "vi_VN": ("越南文", "Vietnamese", "vi-VN"),
    "th_TH": ("泰文", "Thai", "th-TH"),
    "id_ID": ("印尼文", "Indonesian", "id-ID"),
    "ms_MY": ("馬來文", "Malay", "ms-MY"),
    "tl_PH": ("菲律賓文", "Filipino", "fil-PH"),
    "hi_IN": ("印地文", "Hindi", "hi-IN"),
    "bn_IN": ("孟加拉文", "Bengali", "bn-IN"),
    "ta_IN": ("泰米爾文", "Tamil", "ta-IN"),
    "te_IN": ("泰盧固文", "Telugu", "te-IN"),
    "mr_IN": ("馬拉地文", "Marathi", "mr-IN"),
    "gu_IN": ("古吉拉特文", "Gujarati", "gu-IN"),
    "kn_IN": ("卡納達文", "Kannada", "kn-IN"),
    "ml_IN": ("馬拉雅拉姆文", "Malayalam", "ml-IN"),
    "pa_IN": ("旁遮普文", "Punjabi", "pa-IN"),
    "ur_PK": ("烏爾都文", "Urdu", "ur-PK"),
    
    # 中東語言
    "ar_SA": ("阿拉伯文", "Arabic", "ar-SA"),
    "he_IL": ("希伯來文", "Hebrew", "he-IL"),
    "fa_IR": ("波斯文", "Persian", "fa-IR"),
    "tr_TR": ("土耳其文", "Turkish", "tr-TR"),
    
    # 非洲語言
    "sw_KE": ("斯瓦希里文(肯亞)", "Swahili", "sw-KE"),
    "sw_TZ": ("斯瓦希里文(坦尚尼亞)", "Swahili", "sw-TZ"),
    "zu_ZA": ("祖魯文", "Zulu", "zu-ZA"),
}

# 常用語言（用於介面優先顯示）
COMMON_LANGUAGES = [
    "zh_TW", "en_US", "ja_JP", "ko_KR", "zh_CN",
    "de_DE", "fr_FR", "es_ES", "vi_VN", "th_TH"
]


def get_language_choices():
    """取得語言選項清單（用於 Gradio Dropdown）"""
    choices = []
    
    # 先加入常用語言
    for code in COMMON_LANGUAGES:
        if code in LANGUAGES:
            ch_name, en_name, locale = LANGUAGES[code]
            choices.append((f"⭐ {ch_name} ({en_name})", code))
    
    # 加入分隔線
    choices.append(("─" * 20, None))
    
    # 再加入其他語言（按中文名稱排序）
    other_langs = [(code, info) for code, info in LANGUAGES.items() 
                   if code not in COMMON_LANGUAGES]
    other_langs.sort(key=lambda x: x[1][0])
    
    for code, (ch_name, en_name, locale) in other_langs:
        choices.append((f"{ch_name} ({en_name})", code))
    
    return choices


def get_language_info(code: str) -> tuple:
    """取得語言資訊"""
    return LANGUAGES.get(code, ("Unknown", "Unknown", code))
