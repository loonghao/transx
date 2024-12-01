#!/usr/bin/env python
"""Basic usage examples for TransX."""
from transx import TransX

def basic_translation():
    """Basic translation without context."""
    tx = TransX(locales_root="locales")
    tx.current_locale = "zh_CN"
    
    # Basic translations
    print("\n=== Basic Translation Example ===")
    print(f"Simple text: {tx.tr('Hello')}")
    print(f"With parameter: {tx.tr('Hello {name}!', name='张三')}")

def context_translation():
    """Translation with different contexts."""
    tx = TransX(locales_root="locales")
    tx.current_locale = "zh_CN"
    
    # UI Context Example
    print("\n=== UI Context Example ===")
    print(f"Button: {tx.tr('Open', context='button')}")
    print(f"Menu: {tx.tr('Open', context='menu')}")
    
    # Part of Speech Context Example
    print("\n=== Part of Speech Context Example ===")
    print(f"Verb: {tx.tr('Post', context='verb')}")
    print(f"Noun: {tx.tr('Post', context='noun')}")
    
    # Scene Context Example
    print("\n=== Scene Context Example ===")
    print(f"Home: {tx.tr('Welcome', context='home')}")
    print(f"Login: {tx.tr('Welcome', context='login')}")

def parameter_translation():
    """Translation with parameters and context."""
    tx = TransX(locales_root="locales")
    tx.current_locale = "zh_CN"
    
    print("\n=== Parameters with Context Example ===")
    filename = "test.txt"
    print(f"File Menu: {tx.tr('Save {filename}', context='menu', filename=filename)}")
    print(f"Button: {tx.tr('Save {filename}', context='button', filename=filename)}")

def main():
    """Run all examples."""
    try:
        basic_translation()
        context_translation()
        parameter_translation()
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
