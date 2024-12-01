import os
import pytest

from transx import TransX
from transx.formats.po import POFile
from transx.formats.pot import PotExtractor
from transx.formats.mo import compile_po_file

@pytest.fixture
def test_data_dir():
    """Return the path to test data directory."""
    return os.path.join(os.path.dirname(__file__), 'data')

@pytest.fixture
def locales_dir(test_data_dir):
    """Return the path to test locales directory."""
    locales_dir = os.path.join(test_data_dir, 'locales')
    os.makedirs(locales_dir, exist_ok=True)
    return locales_dir

@pytest.fixture
def transx_instance(locales_dir):
    """Return a TransX instance configured for testing."""
    tx = TransX(locales_root=locales_dir)
    tx.current_locale = 'zh_CN'
    return tx

@pytest.fixture
def pot_extractor(locales_dir):
    """Return a POT extractor instance configured for testing."""
    pot_file = os.path.join(locales_dir, 'messages.pot')
    return PotExtractor(pot_file)

@pytest.fixture
def translations():
    """Return test translation data."""
    return {
        'zh_CN': {
            # UI Context translations
            ('Open', 'button'): '打开',
            ('Open', 'menu'): '打开文件',
            ('Save', 'button'): '保存',
            ('Save', 'menu'): '保存文件',
            
            # Part of Speech Context translations
            ('Post', 'verb'): '发布',
            ('Post', 'noun'): '文章',
            
            # Scene Context translations
            ('Welcome', 'home'): '欢迎回来',
            ('Welcome', 'login'): '欢迎登录',
            
            # Context with Parameters
            ('Save {filename}', 'button'): '保存 {filename}',
            ('Save {filename}', 'menu'): '保存文件 {filename}',
            ('Delete {filename}', 'button'): '删除 {filename}',
            ('Delete {filename}', 'menu'): '删除文件 {filename}',
            
            # No Context
            ('Hello', None): '你好',
            ('Goodbye', None): '再见',
            
            # Parameters without Context
            ('Hello, {name}!', None): '你好，{name}！',
            ('Goodbye, {name}!', None): '再见，{name}！',
            
            # Missing Translation (will return original)
            ('Missing', None): '',
            
            # Welcome Messages
            ('Welcome back, {name}!', 'home'): '欢迎回来，{name}！',
            ('Welcome to {app_name}', 'login'): '欢迎使用 {app_name}',
            
            # Error Messages
            ('Error: {msg}', 'error'): '错误：{msg}',
            ('Warning: {msg}', 'warning'): '警告：{msg}',
            
            # Time-based Messages
            ('Good morning', 'greeting'): '早上好',
            ('Good afternoon', 'greeting'): '下午好',
            ('Good evening', 'greeting'): '晚上好',
        },
        'ja_JP': {
            # UI Context translations
            ('Open', 'button'): '開く',
            ('Open', 'menu'): 'ファイルを開く',
            ('Save', 'button'): '保存',
            ('Save', 'menu'): 'ファイルを保存',
            
            # Part of Speech Context translations
            ('Post', 'verb'): '投稿する',
            ('Post', 'noun'): '記事',
            
            # Scene Context translations
            ('Welcome', 'home'): 'おかえりなさい',
            ('Welcome', 'login'): 'ログインへようこそ',
            
            # Context with Parameters
            ('Save {filename}', 'button'): '{filename}を保存',
            ('Save {filename}', 'menu'): '{filename}を保存する',
            ('Delete {filename}', 'button'): '{filename}を削除',
            ('Delete {filename}', 'menu'): '{filename}を削除する',
            
            # No Context
            ('Hello', None): 'こんにちは',
            ('Goodbye', None): 'さようなら',
            
            # Parameters without Context
            ('Hello, {name}!', None): 'こんにちは、{name}さん！',
            ('Goodbye, {name}!', None): 'さようなら、{name}さん！',
            
            # Missing Translation (will return original)
            ('Missing', None): '',
            
            # Welcome Messages
            ('Welcome back, {name}!', 'home'): 'おかえりなさい、{name}さん！',
            ('Welcome to {app_name}', 'login'): '{app_name}へようこそ',
            
            # Error Messages
            ('Error: {msg}', 'error'): 'エラー：{msg}',
            ('Warning: {msg}', 'warning'): '警告：{msg}',
            
            # Time-based Messages
            ('Good morning', 'greeting'): 'おはようございます',
            ('Good afternoon', 'greeting'): 'こんにちは',
            ('Good evening', 'greeting'): 'こんばんは',
        }
    }

@pytest.fixture
def translator(tmpdir, translations):
    """Create a TransX instance with test translations."""
    tx = TransX(locales_root=tmpdir.join("locales"))
    
    # Add translations for each locale
    for locale, trans_dict in translations.items():
        tx.current_locale = locale
        for key, value in trans_dict.items():
            if key[1] is not None:
                msgid, context = key
                tx.add_translation(msgid, value, context=context)
            else:
                tx.add_translation(key[0], value)
    
    return tx


@pytest.fixture(autouse=True)
def setup_translations(tmpdir, translations):
    """Set up translation files before each test."""
    # Create PO files for all locales
    for locale in ['zh_CN', 'ja_JP']:
        locale_dir = os.path.join(str(tmpdir), locale, 'LC_MESSAGES')
        os.makedirs(locale_dir, exist_ok=True)
        
        po_file = os.path.join(locale_dir, 'messages.po')
        po = POFile(po_file, locale=locale)
        
        # Add translations
        for key, msgstr in translations[locale].items():
            if key[1] is not None:
                msgid, context = key
                po.add_translation(msgid, msgstr=msgstr, context=context)
            else:
                po.add_translation(key[0], msgstr=msgstr)
        po.save()
        
        # Compile PO to MO
        mo_file = os.path.join(locale_dir, 'messages.mo')
        compile_po_file(po_file, mo_file)
