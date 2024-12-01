"""
多语言支持演示程序
"""
from transx import TransX

def test_basic_translations(tx):
    """测试基本翻译"""
    print(tx.tr("Hello"))
    print(tx.tr("Welcome {name}", name="Alice"))
    print(tx.tr("Current language is {lang}", lang=tx.current_locale))

def test_workflow_messages(tx):
    """测试工作流相关消息"""
    print("\n=== Workflow Messages ===")
    print(tx.tr("Starting workflow"))
    print(tx.tr("Processing step {step} of {total}", step=1, total=3))
    print(tx.tr("Validating input data"))
    print(tx.tr("Analyzing results"))
    print(tx.tr("Task completed successfully"))

def test_error_messages(tx):
    """测试错误消息"""
    print("\n=== Error Messages ===")
    print(tx.tr("Error: File not found"))
    print(tx.tr("Warning: Low disk space"))
    print(tx.tr("Invalid input: {input}", input="abc123"))
    print(tx.tr("Operation failed: {reason}", reason="timeout"))

def main():
    # 初始化TransX实例，指定语言包目录
    tx = TransX(locales_root='locales')
    
    # 测试不同语言的翻译
    languages = ['en_US', 'zh_CN', 'ja_JP', 'ko_KR']
    
    for lang in languages:
        # 切换语言
        tx.current_locale = lang
        
        # 打印分隔线
        print("\n" + "="*50)
        print(f"Testing language: {lang}")
        print("="*50)
        
        # 运行所有测试
        test_basic_translations(tx)
        test_workflow_messages(tx)
        test_error_messages(tx)

if __name__ == "__main__":
    main()
