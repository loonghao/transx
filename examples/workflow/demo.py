"""Multilingual support demo program."""
# Import local modules
from transx import TransX


def test_basic_translations(tx):
    """Test basic translations."""
    print(tx.tr("Hello"))
    print(tx.tr("Welcome {name}", name="Alice"))
    print(tx.tr("Current language is {lang}", lang=tx.current_locale))

def test_workflow_messages(tx):
    """Test workflow related messages."""
    print("\n=== Workflow Messages ===")
    print(tx.tr("Starting workflow"))
    print(tx.tr("Processing file {filename}", filename="data.txt"))
    print(tx.tr("Workflow completed"))
    print(tx.tr("Validating input data"))
    print(tx.tr("Analyzing results"))
    print(tx.tr("Task completed successfully"))

def test_error_messages(tx):
    """Test error messages."""
    print("\n=== Error Messages ===")
    print(tx.tr("Error: File not found"))
    print(tx.tr("Warning: Low disk space"))
    print(tx.tr("Invalid input: {input}", input="abc123"))
    print(tx.tr("Operation failed: {reason}", reason="timeout"))

def test_unicode_handling(tx):
    """Test unicode handling."""
    print("\n=== Unicode Handling ===")
    print(tx.tr("Hello\nWorld"))
    print(tx.tr("Tab\there"))


def main():
    # Initialize TransX instance with language pack directory
    tx = TransX(locales_root="locales", strict_mode=True)

    # Test translations for different languages
    languages = ["en_US", "zh_CN", "ja_JP", "ko_KR"]

    for lang in languages:
        # Switch language
        tx.current_locale = lang

        # Print separator
        print("\n" + "="*50)
        print(f"Testing language: {lang}")
        print("="*50)

        # Run all tests
        test_basic_translations(tx)
        test_workflow_messages(tx)
        test_error_messages(tx)
        test_unicode_handling(tx)

if __name__ == "__main__":
    main()
