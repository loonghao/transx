"""Test translation functionality."""
import os
import pytest
import tempfile
import shutil
import logging
from transx.formats.mo import compile_po_file
from transx.formats.po import POFile

@pytest.fixture(autouse=True)
def setup_translations(locales_dir, translations):
    """Set up translation files before each test."""
    # Create PO file for zh_CN
    locale = 'zh_CN'
    locale_dir = os.path.join(locales_dir, locale, 'LC_MESSAGES')
    os.makedirs(locale_dir, exist_ok=True)
    
    po_file = os.path.join(locale_dir, 'messages.po')
    po = POFile(po_file, locale=locale)
    
    # Add translations
    for (msgid, context), msgstr in translations[locale].items():
        po.add_translation(msgid, msgstr=msgstr, context=context)
    po.save()
    
    # Compile PO to MO
    mo_file = os.path.join(locale_dir, 'messages.mo')
    compile_po_file(po_file, mo_file)

    # Log the creation of translation files
    logging.debug(f"Translation files created at {locale_dir}")
    logging.debug(f"PO file contents: {po.translations}")

def test_ui_context_translation(transx_instance):
    """Test translations with UI context."""
    assert transx_instance.tr('Open', context='button') == '打开'
    assert transx_instance.tr('Open', context='menu') == '打开文件'

def test_part_of_speech_context(transx_instance):
    """Test translations with part of speech context."""
    assert transx_instance.tr('Post', context='verb') == '发布'
    assert transx_instance.tr('Post', context='noun') == '文章'

def test_scene_context(transx_instance):
    """Test translations with scene context."""
    assert transx_instance.tr('Welcome', context='home') == '欢迎回来'
    assert transx_instance.tr('Welcome', context='login') == '欢迎登录'

def test_context_with_parameters(transx_instance):
    """Test translations with context and parameters."""
    filename = 'test.txt'
    assert transx_instance.tr('Save {filename}', context='button', filename=filename) == '保存 {filename}'.format(filename=filename)
    assert transx_instance.tr('Save {filename}', context='menu', filename=filename) == '保存文件 {filename}'.format(filename=filename)

def test_translation_without_context(transx_instance):
    """Test translations without context."""
    assert transx_instance.tr('Hello') == '你好'
    assert transx_instance.tr('Goodbye') == '再见'

def test_translation_with_only_parameters(transx_instance):
    """Test translations with parameters but no context."""
    name = 'Alice'
    filename = 'test.txt'
    print(transx_instance.current_locale, transx_instance.path)
    assert transx_instance.tr('Hello {name}', name=name) == '你好 {name}'.format(name=name)
    assert transx_instance.tr('File {filename} saved', filename=filename) == '文件 {filename} 已保存'.format(filename=filename)

def test_missing_translation(transx_instance):
    """Test behavior when translation is missing."""
    missing_text = 'This text has no translation'
    assert transx_instance.tr(missing_text) == missing_text

def test_cross_version_compatibility(transx_instance):
    """Test translation compatibility across Python versions."""
    # Basic translation test that should work across all versions
    assert transx_instance.tr('Open', context='button') == '打开'

def test_pot_extraction(pot_extractor):
    """Test POT file extraction."""
    # Create a temporary directory for test files
    temp_dir = tempfile.mkdtemp()
    try:
        # Create a test Python file
        test_file = os.path.join(temp_dir, 'test_source.py')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('from transx import TransX\n')
            f.write('tx = TransX(locales_root="locales")\n')
            f.write('print(tx.tr("Open", context="button"))\n')
            f.write('print(tx.tr("Welcome", context="home"))\n')
        
        # Extract messages
        pot_extractor.scan_file(test_file)
        pot_extractor.save_pot()
        
        # Verify POT file exists
        assert os.path.exists(pot_extractor.output_file)
    finally:
        # Clean up
        shutil.rmtree(temp_dir)

def test_po_file_creation(locales_dir, translations):
    """Test PO file creation and translation."""
    locale = 'zh_CN'
    locale_dir = os.path.join(locales_dir, locale, 'LC_MESSAGES')
    os.makedirs(locale_dir, exist_ok=True)
    
    po_file = os.path.join(locale_dir, 'messages.po')
    po = POFile(po_file, locale=locale)
    
    # Add translations
    for (msgid, context), msgstr in translations['zh_CN'].items():
        po.add_translation(msgid, msgstr, context=context)
    
    po.save()
    assert os.path.exists(po_file)

def test_mo_compilation(locales_dir):
    """Test MO file compilation."""
    locale = 'zh_CN'
    locale_dir = os.path.join(locales_dir, locale, 'LC_MESSAGES')
    po_file = os.path.join(locale_dir, 'messages.po')
    mo_file = os.path.join(locale_dir, 'messages.mo')
    
    # Ensure PO file exists before compilation
    if not os.path.exists(po_file):
        pytest.skip("PO file not found")
    
    compile_po_file(po_file, mo_file)
    assert os.path.exists(mo_file)


def test_cross_version_compatibility(transx_instance, python_version):
    """Test translation compatibility across Python versions."""
    # Basic translation test that should work across all versions
    assert transx_instance.tr('Open', context='button') == '打开'

def test_multilanguage_context_switching(translator, translations):
    """Test switching between different languages while maintaining context."""
    
    test_cases = [
        ('Open', 'button'),
        ('Open', 'menu'),
        ('Save', 'button'),
        ('Save', 'menu')
    ]
    locales = ['en', 'zh_CN', 'ja_JP', 'ko_KR']
    
    for msgid, context in test_cases:
        key = f"{msgid}|{context}"
        for locale in locales:
            translator.current_locale = locale
            result = translator.tr(msgid, context=context)
            expected = translations[locale][key]
            assert result == expected, f"Failed for locale {locale}, context {context}, message {msgid}"

def test_multilanguage_welcome_context(translator, translations):
    """Test welcome message translations in different contexts and languages."""
    
    test_cases = [('Welcome', 'login'), ('Welcome', 'home')]
    locales = ['en', 'zh_CN', 'ja_JP', 'ko_KR']
    
    for msgid, context in test_cases:
        key = f"{msgid}|{context}"
        for locale in locales:
            translator.current_locale = locale
            result = translator.tr(msgid, context=context)
            expected = translations[locale][key]
            assert result == expected, "Failed for locale {locale}, context {context}".format(locale=locale, context=context)

def test_multilanguage_parameters(translator, translations):
    """Test parameter substitution across different languages."""
    
    test_cases = [
        ('Hello {name}', {'name': 'Alice'}),
        ('Save {filename}', {'filename': 'test.txt'}),
        ('File {filename} saved', {'filename': 'data.txt'})
    ]
    locales = ['en', 'zh_CN', 'ja_JP', 'ko_KR']
    
    for msgid, params in test_cases:
        for locale in locales:
            translator.current_locale = locale
            result = translator.tr(msgid, **params)
            
            # Get the translation template
            template = translations[locale][msgid]
            # Format the template with the parameters
            expected = template.format(**params)
            
            assert result == expected, "Failed for locale {locale}, message {msgid}".format(locale=locale, msgid=msgid)

def test_multilanguage_part_of_speech(translator, translations):
    """Test part of speech context translations across languages."""
    
    test_cases = [('Post', 'verb'), ('Post', 'noun')]
    locales = ['en', 'zh_CN', 'ja_JP', 'ko_KR']
    
    for msgid, context in test_cases:
        key = f"{msgid}|{context}"
        for locale in locales:
            translator.current_locale = locale
            result = translator.tr(msgid, context=context)
            expected = translations[locale][key]
            assert result == expected, "Failed for locale {locale}, context {context}".format(locale=locale, context=context)

def test_rapid_language_switching(translator, translations):
    """Test rapid switching between languages while maintaining context."""
    
    test_cases = [
        ('Open', 'button'),
        ('Save', 'menu'),
        ('Welcome', 'login'),
        ('Post', 'verb')
    ]
    locales = ['en', 'zh_CN', 'ja_JP', 'ko_KR']
    
    # Switch languages multiple times for each test case
    for msgid, context in test_cases:
        key = f"{msgid}|{context}"
        for _ in range(3):  # Test multiple switches
            for locale in locales:
                translator.current_locale = locale
                result = translator.tr(msgid, context=context)
                expected = translations[locale][key]
                assert result == expected, "Failed for locale {locale}, context {context}, message {msgid}".format(locale=locale, context=context, msgid=msgid)

def test_translation_file_loading(transx_instance):
    """Test that translation files are loaded correctly."""
    assert transx_instance.current_locale == 'zh_CN'
    assert transx_instance.tr('Hello') == '你好'
    assert transx_instance.tr('Goodbye') == '再见'

def test_translation_with_various_contexts(transx_instance):
    """Test translations with various contexts and parameters."""
    assert transx_instance.tr('Save {filename}', context='button', filename='test.txt') == '保存 test.txt'
    assert transx_instance.tr('Save {filename}', context='menu', filename='test.txt') == '保存文件 test.txt'
    assert transx_instance.tr('Hello {name}', name='Alice') == '你好 Alice'

def test_missing_translation_behavior(transx_instance):
    """Test behavior when translation is missing."""
    missing_text = 'This text has no translation'
    assert transx_instance.tr(missing_text) == missing_text

def test_error_handling_in_translation(transx_instance):
    """Test error handling when translation parameters are missing."""
    try:
        transx_instance.tr('Hello {name}')
    except KeyError as e:
        assert str(e) == "'name'"

def test_translation_across_python_versions(transx_instance):
    """Test translation compatibility across Python versions."""
    # Basic translation test that should work across all versions
    assert transx_instance.tr('Open', context='button') == '打开'

def test_load_catalog(tmp_path):
    # Create a test catalog
    catalog_path = tmp_path / "test.mo"
    tx = TransX()
    
    # Test loading non-existent catalog
    assert tx.load_catalog(str(catalog_path)) is False
    
    # Create and compile a test catalog
    po_file = POFile()
    po_file.add_message("Hello", "你好")
    po_file.add_message("Open", "打开", context="button")
    po_file.save(str(tmp_path / "test.po"))
    compile_po_file(str(tmp_path / "test.po"), str(catalog_path))
    
    # Test loading existing catalog
    assert tx.load_catalog(str(catalog_path)) is True
    assert tx.tr("Hello") == "你好"
    assert tx.tr("Open", context="button") == "打开"

def test_load_catalogs_dir(tmp_path):
    # Create test catalogs directory
    catalogs_dir = tmp_path / "locale" / "zh_CN" / "LC_MESSAGES"
    catalogs_dir.mkdir(parents=True)
    
    # Create and compile test catalogs
    po_file = POFile()
    po_file.add_message("Hello", "你好")
    po_file.save(str(catalogs_dir / "messages.po"))
    compile_po_file(str(catalogs_dir / "messages.po"), str(catalogs_dir / "messages.mo"))
    
    # Test loading catalogs directory
    tx = TransX(locales_root=str(tmp_path))
    tx.current_locale = "zh_CN"
    assert tx.tr("Hello") == "你好"

def test_invalid_locale_handling(transx_instance):
    """Test handling of invalid locale."""
    with pytest.raises(LocaleNotFoundError):
        transx_instance.current_locale = 'invalid_locale'
        transx_instance.tr('Hello')

def test_unicode_handling(transx_instance):
    """Test handling of unicode characters in translations."""
    assert transx_instance.tr('Hello') == '你好'
    assert transx_instance.tr('Welcome') == '欢迎'

def test_empty_context_handling(transx_instance):
    """Test handling of empty context."""
    assert transx_instance.tr('Open', context='') == transx_instance.tr('Open')

def test_none_context_handling(transx_instance):
    """Test handling of None context."""
    assert transx_instance.tr('Open', context=None) == transx_instance.tr('Open')
