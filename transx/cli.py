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
from transx.api.translate import GoogleTranslator
from transx.api.translate import translate_po_file
from transx.api.translate import translate_po_files
from transx.constants import DEFAULT_LANGUAGES
from transx.constants import DEFAULT_LOCALES_DIR
from transx.constants import DEFAULT_MESSAGES_DOMAIN
from transx.constants import MO_FILE_EXTENSION
from transx.constants import POT_FILE_EXTENSION
from transx.internal.filesystem import walk_with_gitignore
from transx.internal.logging import get_logger
from transx.internal.logging import setup_logging


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

    if not os.path.exists(args.source_path):
        logger.error("Path does not exist: %s", args.source_path)
        return 1

    # Ensure output directory exists
    try:
        os.makedirs(os.path.dirname(args.output))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # Collect source files using walk_with_gitignore
    if os.path.isdir(args.source_path):
        source_files = walk_with_gitignore(args.source_path, ["*.py"])
    else:
        source_files = [args.source_path]

    try:
        # Create and use POT extractor
        with PotExtractor(pot_file=args.output, source_files=source_files) as extractor:
            logger.info("Extracting messages from %d source files...", len(source_files))
            extractor.extract_messages()
            extractor.save_pot(
                project=args.project,
                version=args.version,
                copyright_holder=args.copyright,
                bugs_address=args.bugs_address
            )

        # Generate language files
        languages = args.languages.split(",") if args.languages else DEFAULT_LANGUAGES
        locales_dir = os.path.abspath(args.output_dir)

        # Create updater for language files
        updater = PotUpdater(args.output, locales_dir)
        updater.create_language_catalogs(languages)

        logger.info("POT file created and language files updated: %s", args.output)
        return 0

    except Exception as e:
        logger.error("Error processing files: %s", str(e))
        return 1


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
    logger = get_logger(__name__)
    success = True

    # If no PO files specified, use default pattern
    if not args.po_files:
        base_dir = os.path.abspath(args.directory)
        pattern = os.path.join(base_dir, "locales", "*", "LC_MESSAGES", "messages.po")
        po_files = glob.glob(pattern)
        if not po_files:
            logger.warning("No .po files found matching pattern: %s", pattern)
            return 0
    else:
        po_files = args.po_files

    for po_file in po_files:
        if not os.path.exists(po_file):
            logger.error("PO file not found: %s", po_file)
            success = False
            continue

        # Build MO file path (in the same directory as PO file)
        mo_file = os.path.splitext(po_file)[0] + MO_FILE_EXTENSION
        logger.info("Compiling %s to %s", po_file, mo_file)

        try:
            # Ensure the directory exists
            try:
                os.makedirs(os.path.dirname(mo_file))
            except OSError:
                if not os.path.isdir(os.path.dirname(mo_file)):
                    raise
            compile_po_file(po_file, mo_file)
        except Exception as e:
            logger.error("Error compiling %s: %s", po_file, e)
            success = False

    return 0 if success else 1


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
    translator = GoogleTranslator()
    logger = get_logger(__name__)

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
