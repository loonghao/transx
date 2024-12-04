"""Command-line interface for transx."""
# Import built-in modules
import argparse
import errno
import logging
import os
import sys

# Import local modules
from transx.api.mo import compile_po_file
from transx.api.pot import PotExtractor
from transx.api.pot import PotUpdater
from transx.constants import DEFAULT_LOCALES_DIR
from transx.constants import DEFAULT_MESSAGES_DOMAIN
from transx.constants import MO_FILE_EXTENSION
from transx.constants import POT_FILE_EXTENSION


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )
    return logging.getLogger(__name__)


def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="TransX - Translation Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # extract command
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract translatable messages from source files to POT file"
    )
    extract_parser.add_argument(
        "source_path",
        help="Source file or directory to extract messages from"
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
        help="Comma-separated list of languages to generate (default: en,zh_CN,ja_JP,ko_KR)"
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
        help="Path to the POT file"
    )
    update_parser.add_argument(
        "-l", "--languages",
        help="Comma-separated list of languages to update (default: en,zh_CN,ja_JP,ko_KR)"
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
        nargs="+",
        help="PO files to compile"
    )

    return parser


def extract_command(args):
    """Execute extract command."""
    logger = logging.getLogger(__name__)

    if not os.path.exists(args.source_path):
        logger.error("Path does not exist: %s", args.source_path)
        return 1

    # Ensure output directory exists
    try:
        os.makedirs(os.path.dirname(args.output))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # Collect source files
    source_files = []
    if os.path.isdir(args.source_path):
        for root, _, files in os.walk(args.source_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    source_files.append(file_path)
    else:
        source_files.append(args.source_path)

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
        languages = args.languages.split(",") if args.languages else ["en", "zh_CN", "ja_JP", "ko_KR"]
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
    logger = logging.getLogger(__name__)

    if not os.path.exists(args.pot_file):
        logger.error("POT file not found: %s", args.pot_file)
        return 1

    # Create POT updater
    try:
        updater = PotUpdater(args.pot_file, args.output_dir)
        languages = args.languages.split(",") if args.languages else ["en", "zh_CN", "ja_JP", "ko_KR"]
        updater.create_language_catalogs(languages)
        logger.info("Language files updated.")
        return 0
    except Exception as e:
        logger.error("Error updating language files: %s", e)
        return 1


def compile_command(args):
    """Execute compile command."""
    logger = logging.getLogger(__name__)
    success = True

    for po_file in args.po_files:
        if not os.path.exists(po_file):
            logger.error("PO file not found: %s", po_file)
            success = False
            continue

        # Build MO file path (in the same directory as PO file)
        mo_file = os.path.splitext(po_file)[0] + MO_FILE_EXTENSION
        logger.info("Compiling %s to %s", po_file, mo_file)

        try:
            compile_po_file(po_file, mo_file)
        except Exception as e:
            logger.error("Error compiling %s: %s", po_file, e)
            success = False

    return 0 if success else 1


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
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
