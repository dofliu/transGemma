"""
TranslateGemma 翻譯測試腳本
============================
透過命令列互動測試 TranslateGemma 翻譯模型

使用方式：
    python test_translate.py

功能：
    1. 多語言翻譯
    2. 語言選擇選單
    3. 翻譯歷史記錄
"""

import ollama
import sys

# ============ 支援的語言清單 ============
LANGUAGES = {
    # 常用語言
    "1": ("繁體中文", "Traditional Chinese", "zh_TW"),
    "2": ("簡體中文", "Simplified Chinese", "zh_CN"),
    "3": ("英文", "English", "en-US"),
    "4": ("日文", "Japanese", "ja-JP"),
    "5": ("韓文", "Korean", "ko-KR"),
    "6": ("德文", "German", "de-DE"),
    "7": ("法文", "French", "fr-FR"),
    "8": ("西班牙文", "Spanish", "es-ES"),
    "9": ("義大利文", "Italian", "it-IT"),
    "10": ("俄文", "Russian", "ru-RU"),
    "11": ("葡萄牙文", "Portuguese", "pt-BR"),
    "12": ("越南文", "Vietnamese", "vi-VN"),
    "13": ("泰文", "Thai", "th-TH"),
    "14": ("印尼文", "Indonesian", "id-ID"),
    "15": ("阿拉伯文", "Arabic", "ar-SA"),
}


def show_languages():
    """顯示語言選擇選單"""
    print("\n" + "=" * 50)
    print("【語言選擇】")
    print("=" * 50)
    for key, (ch_name, en_name, code) in LANGUAGES.items():
        print(f"  {key:>2}. {ch_name} ({en_name})")
    print("=" * 50)


def get_prompt(text: str, source_lang: tuple, target_lang: tuple) -> str:
    """生成翻譯 prompt"""
    src_name, src_en, src_code = source_lang
    tgt_name, tgt_en, tgt_code = target_lang
    
    # 繁體中文特殊處理
    if tgt_code == "zh_TW":
        prompt = f"""You are a professional {src_en} ({src_code}) to Traditional Chinese (Taiwan) translator.

IMPORTANT RULES:
1. You MUST output ONLY Traditional Chinese characters (繁體字) as used in Taiwan.
2. DO NOT use any Simplified Chinese characters (简体字).
3. Examples of correct Traditional vs incorrect Simplified:
   - 嗎 (correct) vs 吗 (wrong)
   - 著 (correct) vs 着 (wrong)
   - 這 (correct) vs 这 (wrong)
   - 裡 (correct) vs 里 (wrong)
   - 說 (correct) vs 说 (wrong)
   - 軟體 (correct) vs 软件 (wrong)
   - 網路 (correct) vs 网络 (wrong)

Please provide ONLY the Traditional Chinese translation without any additional explanations.

Translate the following text:

{text}"""
    else:
        prompt = f"""You are a professional {src_en} ({src_code}) to {tgt_en} ({tgt_code}) translator.
Your goal is to accurately convey the meaning and nuances of the original {src_en} text 
while adhering to {tgt_en} grammar, style, and conventions.

Please provide ONLY the {tgt_en} translation without any additional explanations or commentary.

Please translate the following text:

{text}"""
    
    return prompt


def translate(text: str, source_lang: tuple, target_lang: tuple) -> str:
    """執行翻譯"""
    prompt = get_prompt(text, source_lang, target_lang)
    
    print(f"\n🔄 翻譯中... ({source_lang[0]} → {target_lang[0]})")
    
    try:
        response = ollama.chat(
            model='translategemma',
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response['message']['content']
    except Exception as e:
        return f"❌ 翻譯錯誤: {str(e)}"


def translate_streaming(text: str, source_lang: tuple, target_lang: tuple):
    """執行串流翻譯（即時顯示）"""
    prompt = get_prompt(text, source_lang, target_lang)
    
    print(f"\n🔄 翻譯中... ({source_lang[0]} → {target_lang[0]})")
    print("-" * 40)
    
    try:
        stream = ollama.chat(
            model='translategemma',
            messages=[{'role': 'user', 'content': prompt}],
            stream=True
        )
        
        result = ""
        for chunk in stream:
            content = chunk['message']['content']
            print(content, end='', flush=True)
            result += content
        
        print("\n" + "-" * 40)
        return result
    except Exception as e:
        return f"❌ 翻譯錯誤: {str(e)}"


def main():
    """主程式"""
    print("""
╔══════════════════════════════════════════════════════╗
║         TranslateGemma 翻譯測試工具                  ║
║         支援 55 種語言互譯                           ║
╚══════════════════════════════════════════════════════╝
    """)
    
    # 預設語言設定
    source_lang = LANGUAGES["3"]  # 英文
    target_lang = LANGUAGES["1"]  # 繁體中文
    use_streaming = True
    
    print(f"📌 目前設定: {source_lang[0]} → {target_lang[0]}")
    print(f"📌 串流模式: {'開啟' if use_streaming else '關閉'}")
    
    print("""
指令說明:
  /s  - 設定來源語言
  /t  - 設定目標語言
  /swap - 交換來源與目標語言
  /stream - 切換串流模式
  /list - 顯示語言清單
  /quit - 離開程式
  
直接輸入文字即可翻譯
""")
    
    history = []
    
    while True:
        try:
            user_input = input("\n📝 請輸入文字 (或指令): ").strip()
            
            if not user_input:
                continue
            
            # 處理指令
            if user_input.lower() == "/quit":
                print("👋 感謝使用，再見！")
                break
            
            elif user_input.lower() == "/list":
                show_languages()
            
            elif user_input.lower() == "/s":
                show_languages()
                choice = input("請選擇來源語言編號: ").strip()
                if choice in LANGUAGES:
                    source_lang = LANGUAGES[choice]
                    print(f"✅ 來源語言已設為: {source_lang[0]}")
                else:
                    print("❌ 無效的選擇")
            
            elif user_input.lower() == "/t":
                show_languages()
                choice = input("請選擇目標語言編號: ").strip()
                if choice in LANGUAGES:
                    target_lang = LANGUAGES[choice]
                    print(f"✅ 目標語言已設為: {target_lang[0]}")
                else:
                    print("❌ 無效的選擇")
            
            elif user_input.lower() == "/swap":
                source_lang, target_lang = target_lang, source_lang
                print(f"🔄 語言已交換: {source_lang[0]} → {target_lang[0]}")
            
            elif user_input.lower() == "/stream":
                use_streaming = not use_streaming
                print(f"📌 串流模式: {'開啟' if use_streaming else '關閉'}")
            
            elif user_input.startswith("/"):
                print("❌ 未知指令，請輸入 /list 查看語言或直接輸入文字翻譯")
            
            else:
                # 執行翻譯
                if use_streaming:
                    result = translate_streaming(user_input, source_lang, target_lang)
                else:
                    result = translate(user_input, source_lang, target_lang)
                    print(f"\n📖 翻譯結果:\n{result}")
                
                # 儲存歷史
                history.append({
                    "source": user_input,
                    "target": result,
                    "from": source_lang[0],
                    "to": target_lang[0]
                })
        
        except KeyboardInterrupt:
            print("\n\n👋 程式中斷，再見！")
            break
        except Exception as e:
            print(f"\n❌ 發生錯誤: {e}")


if __name__ == "__main__":
    main()
