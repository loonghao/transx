"""更新翻译文件
"""
import os
from transx.formats.pot import PotExtractor

def update_translations():
    """更新所有语言的翻译文件"""
    # 设置文件路径
    pot_file = os.path.join(os.path.abspath("locales"), "messages.pot")
    if not os.path.exists(pot_file):
        print(f"Error: POT file not found: {pot_file}")
        return

    # 创建POT提取器并加载
    extractor = PotExtractor(pot_file)
    extractor.messages.load(pot_file)

    # 生成语言文件
    languages = ["zh_CN", "ja", "ko", "fr", "es_ES"]
    locales_dir = os.path.abspath("locales")
    extractor.generate_language_files(languages, locales_dir)
    print("Language files updated.")

if __name__ == "__main__":
    update_translations()
