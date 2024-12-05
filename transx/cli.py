"""Command-line interface for transx."""
# Import built-in modules
import argparse
import errno
import glob
import os
import sys

# Import local modules
from transx.api.mo import compile_po_file
from transx.api.pot import PotExtractor
from transx.api.pot import PotUpdater
from transx.constants import DEFAULT_LANGUAGES
from transx.constants import DEFAULT_LOCALES_DIR
from transx.constants import DEFAULT_MESSAGES_DOMAIN
from transx.constants import MO_FILE_EXTENSION
from transx.constants import POT_FILE_EXTENSION
from transx.internal.logging import get_logger
from transx.internal.logging import setup_logging
from transx.internal.filesystem import walk_with_gitignore


def create_parser():
    """Create command line argument parser."""
    examples = """
examples:
    # Extract messages from source files (default: current directory)
    transx extract

    # Extract messages from specific source
    transx extract src/myapp -o locales/messages.pot -p "My App" -v "1.0"

    # Update PO files in default locations (locales/*)
    transx update

    # Update PO files with specific POT file
    transx update path/to/messages.pot -l "en,zh_CN,ja_JP"

    # Compile all PO files in default locations
    transx compile

    # Compile PO files from specific directory
    transx compile -d /path/to/project

    # Compile specific PO files
    transx compile path/to/file1.po path/to/file2.po

    # List available locales
    transx list

    # Translate all PO files in locales directory
    transx translate

    # Translate specific PO files
    transx translate path/to/messages.po -t zh_CN

    # Translate PO files with specific languages
    transx translate -l "en,zh_CN,ja_JP"
    """

    parser = argparse.ArgumentParser(
        description="TransX - Translation Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=examples
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # extract command
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract translatable messages from source files to POT file"
    )
    extract_parser.add_argument(
        "source_path",
        nargs="?",
        default=".",
        help="Source file or directory to extract messages from (default: current directory)"
    )
    extract_parser.add_argument(
        "-o", "--output",
        default=os.path.join(DEFAULT_LOCALES_DIR, DEFAULT_MESSAGES_DOMAIN + POT_FILE_EXTENSION),
        help="Output path for POT file (default: %s/%s)" % (DEFAULT_LOCALES_DIR, DEFAULT_MESSAGES_DOMAIN + POT_FILE_EXTENSION)
    )
    extract_parser.add_argument(
        "-p", "--project",
        default="Untitled",
        help="Project name (default: Untitled)"
    )
    extract_parser.add_argument(
        "-v", "--version",
        default="1.0",
        help="Project version (default: 1.0)"
    )
    extract_parser.add_argument(
        "-c", "--copyright",
        default="",
        help="Copyright holder"
    )
    extract_parser.add_argument(
        "-b", "--bugs-address",
        default="",
        help="Bug report email address"
    )
    extract_parser.add_argument(
        "-l", "--languages",
        help="Comma-separated list of languages to generate (default: %s)" % ",".join(DEFAULT_LANGUAGES)
    )
    extract_parser.add_argument(
        "-d", "--output-dir",
        default=DEFAULT_LOCALES_DIR,
        help="Output directory for language files (default: %s)" % DEFAULT_LOCALES_DIR
    )

    # update command
    update_parser = subparsers.add_parser(
        "update",
        help="Update or create PO files for specified languages"
    )
    update_parser.add_argument(
        "pot_file",
        nargs="?",
        default=os.path.join(DEFAULT_LOCALES_DIR, DEFAULT_MESSAGES_DOMAIN + POT_FILE_EXTENSION),
        help="Path to the POT file (default: locales/messages.pot)"
    )
    update_parser.add_argument(
        "-l", "--languages",
        help="Comma-separated list of languages to update (default: %s)" % ",".join(DEFAULT_LANGUAGES)
    )
    update_parser.add_argument(
        "-o", "--output-dir",
        default=DEFAULT_LOCALES_DIR,
        help="Output directory for PO files (default: %s)" % DEFAULT_LOCALES_DIR
    )

    # compile command
    compile_parser = subparsers.add_parser(
        "compile",
        help="Compile PO files to MO files"
    )
    compile_parser.add_argument(
        "po_files",
        nargs="*",
        help="PO files to compile (default: locales/*/LC_MESSAGES/messages.po)"
    )
    compile_parser.add_argument(
        "-d", "--directory",
        default=".",
        help="Base directory to search for PO files (default: current directory)"
    )

    # list command
    list_parser = subparsers.add_parser(
        "list",
        help="List available locales in the project"
    )
    list_parser.add_argument(
        "-d", "--directory",
        default=DEFAULT_LOCALES_DIR,
        help="Base directory to search for locales (default: %s)" % DEFAULT_LOCALES_DIR
    )

    # translate command
    translate_parser = subparsers.add_parser(
        "translate",
        help="Translate PO files using Google Translate"
    )
    translate_parser.add_argument(
        "files",
        nargs="*",
        help="PO files to translate (default: all PO files in locales/*)"
    )
    translate_parser.add_argument(
        "-l", "--languages",
        help="Comma-separated list of languages to translate (default: %s)" % ",".join(DEFAULT_LANGUAGES)
    )
    translate_parser.add_argument(
        "-d", "--directory",
        default=DEFAULT_LOCALES_DIR,
        help="Base directory to search for PO files (default: %s)" % DEFAULT_LOCALES_DIR
    )
    translate_parser.add_argument(
        "-s", "--source-lang",
        default="auto",
        help="Source language code (default: auto)"
    )
    translate_parser.add_argument(
        "-t", "--target-lang",
        help="Target language code (required if specific files are provided)"
    )

    return parser


def extract_command(args):
    """Execute extract command."""
    logger = get_logger(__name__)

    # Find Python source files
    source_files = []
    if os.path.isfile(args.source_path):
        source_files = [args.source_path]
    else:
        source_files = walk_with_gitignore(args.source_path, ['*.py'])

    if not source_files:
        logger.warning("No Python source files found in %s", args.source_path)
        return 1

    # Create output directory if not exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Extract messages
    extractor = PotExtractor(
        project=args.project,
        version=args.version,
        copyright=args.copyright,
        bugs_address=args.bugs_address
    )
    
    for source_file in source_files:
        try:
            extractor.extract_from_file(source_file)
        except Exception as e:
            logger.error("Failed to extract messages from %s: %s", source_file, str(e))
            return 1

    # Write POT file
    try:
        extractor.write_pot_file(args.output)
        logger.info("Created POT file: %s", args.output)
    except Exception as e:
        logger.error("Failed to write POT file: %s", str(e))
        return 1

    # Create PO files if languages specified
    if args.languages:
        languages = args.languages.split(",")
        try:
            updater = PotUpdater(args.output)
            updater.create_or_update_po_files(languages, args.output_dir)
            logger.info("Created PO files for languages: %s", ", ".join(languages))
        except Exception as e:
            logger.error("Failed to create PO files: %s", str(e))
            return 1

    return 0


def update_command(args):
    """Execute update command."""
    logger = get_logger(__name__)

    try:
        if not os.path.exists(args.pot_file):
            logger.error("POT file not found: %s", args.pot_file)
            return 1

        updater = PotUpdater(args.pot_file, args.output_dir)

        # If no languages specified, discover from locales directory
        if not args.languages:
            # Import built-in modules
            import glob
            locale_pattern = os.path.join(args.output_dir, "*")
            locales = [os.path.basename(p) for p in glob.glob(locale_pattern) if os.path.isdir(p)]
            if not locales:
                logger.error("No language directories found in %s", args.output_dir)
                return 1
            args.languages = ",".join(locales)

        languages = [lang.strip() for lang in args.languages.split(",") if lang.strip()]

        # Create language catalogs
        updater.create_language_catalogs(languages)

        return 0
    except Exception as e:
        logger.error("Error updating language files: %s", e)
        return 1


def compile_command(args):
    """Execute compile command."""
    po_files = []
    
    # If specific files provided
    if args.po_files:
        po_files.extend(args.po_files)
    else:
        # Find all PO files in directory
        search_dir = args.directory if args.directory else "."
        po_files = walk_with_gitignore(search_dir, ['*.po'])

    if not po_files:
        logger.warning("No PO files found")
        return 1

    for po_file in po_files:
        try:
            mo_file = os.path.splitext(po_file)[0] + MO_FILE_EXTENSION
            compile_po_file(po_file, mo_file)
            logger.info("Compiled %s -> %s", po_file, mo_file)
        except Exception as e:
            logger.error("Failed to compile %s: %s", po_file, str(e))
            return 1

    return 0


def list_command(args):
    """Execute list command."""
    logger = get_logger(__name__)

    # Check if directory exists first
    if not os.path.exists(args.directory):
        logger.error("Directory not found: %s", args.directory)
        return 1

    # Import local modules
    from transx import TransX

    try:
        tx = TransX(locales_root=args.directory)
        locales = tx.available_locales

        if not locales:
            logger.info("No locales found in: %s", args.directory)
            return 0

        logger.info("Available locales (%d):", len(locales))
        for locale in locales:
            logger.info("  - %s", locale)
        return 0

    except Exception as e:
        logger.error("Error listing locales: %s", str(e))
        return 1


def translate_command(args):
    """Execute translate command."""
    from transx.api.translate import GoogleTranslator, translate_po_files, translate_po_file
    import os

    translator = GoogleTranslator()
    
    # If specific files are provided
    if args.files:
        if not args.target_lang:
            logger.error("Target language (-t/--target-lang) is required when translating specific files")
            return 1
            
        for file_pattern in args.files:
            # Handle glob patterns
            if "*" in file_pattern:
                files = glob.glob(file_pattern)
            else:
                files = [file_pattern]
                
            for file_path in files:
                if not os.path.isfile(file_path):
                    logger.warning("File not found: %s", file_path)
                    continue
                    
                try:
                    translate_po_file(file_path, args.target_lang, translator=translator)
                    logger.info("Translated %s to %s", file_path, args.target_lang)
                except Exception as e:
                    logger.error("Failed to translate %s: %s", file_path, str(e))
    
    # If no files provided, translate all PO files in locales directory
    else:
        languages = args.languages.split(",") if args.languages else DEFAULT_LANGUAGES
        pot_file = os.path.join(args.directory, DEFAULT_MESSAGES_DOMAIN + POT_FILE_EXTENSION)
        
        if not os.path.isfile(pot_file):
            logger.error("POT file not found: %s", pot_file)
            return 1
            
        try:
            translate_po_files(pot_file, languages, args.directory, translator=translator)
            logger.info("Successfully translated PO files for languages: %s", ", ".join(languages))
        except Exception as e:
            logger.error("Failed to translate PO files: %s", str(e))
            return 1
    
    return 0


def main():
    """Main entry function."""
    # Setup logging
    setup_logging()

    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "extract":
        return extract_command(args)
    elif args.command == "update":
        return update_command(args)
    elif args.command == "compile":
        return compile_command(args)
    elif args.command == "list":
        return list_command(args)
    elif args.command == "translate":
        return translate_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
