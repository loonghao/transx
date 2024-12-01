"""
提取需要翻译的消息到POT文件
"""
import os
from transx.formats.pot import PotExtractor

def extract_messages():
    """从源代码中提取需要翻译的消息到POT文件"""
    # 设置POT文件路径
    pot_file = os.path.join(os.path.abspath('locales'), 'messages.pot')
    
    # 确保locales目录存在
    os.makedirs(os.path.abspath('locales'), exist_ok=True)
    
    # 创建POT提取器
    extractor = PotExtractor(pot_file)
    
    # 扫描源代码文件
    source_files = [os.path.abspath('demo.py')]  # 添加所有需要扫描的源文件
    for file in source_files:
        if os.path.exists(file):
            print(f"Scanning {file} for translatable messages...")
            extractor.scan_file(file)
        else:
            print(f"Warning: {file} does not exist")
    
    # 保存POT文件，并设置项目信息
    extractor.save_pot(
        project='Workflow Demo',
        version='1.0',
        copyright_holder='TransX',
        bugs_address='transx@example.com'
    )
    


if __name__ == '__main__':
    extract_messages()
