#!/usr/bin/env python
"""Regression tests for GH #39 - duplicate / stale data in .pot files.

Re-running ``extract`` used to:

* append another copy of the header comment block on every run,
* emit the same ``#:`` location reference twice,
* keep line numbers of strings that had moved or been deleted.

The tests below run the extractor repeatedly and assert the generated POT is
stable and free of stale references.
"""

# Import future modules
from __future__ import unicode_literals

# Import built-in modules
import os
import re

# Import third-party modules
import pytest

# Import local modules
from transx.api.pot import POTFile
from transx.api.pot import PotExtractor
from transx.constants import DEFAULT_CHARSET
from transx.internal.filesystem import normalize_path
from transx.internal.filesystem import read_file

HEADER_MARKER = "# Translations template for PROJECT."


def _write(path, text):
    """Write a UTF-8 text file, creating parent directories when needed."""
    directory = os.path.dirname(str(path))
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(str(path), "w", encoding="utf-8") as handle:
        handle.write(text)


def _extract(source_files, pot_path):
    """Run a full extract cycle over ``source_files`` into ``pot_path``."""
    with PotExtractor(source_files=list(source_files), pot_file=str(pot_path)) as extractor:
        extractor.extract_messages()


def _read(path):
    return read_file(str(path), encoding=DEFAULT_CHARSET)


def _location_lines(content):
    """Return every ``#:`` reference line in the POT content."""
    return [line for line in content.splitlines() if line.startswith("#:")]


def _locations_for(content, msgid):
    """Return the ``#:`` references attached to ``msgid``.

    Entries are separated by blank lines, and the ``#:`` comments come *before*
    their ``msgid``, so locations are buffered until the msgid is known.
    """
    wanted = 'msgid "%s"' % msgid
    pending = []
    for block in content.split("\n\n"):
        locations = []
        has_wanted = False
        for line in block.splitlines():
            if line.startswith("#:"):
                locations.append(line[2:].strip())
            elif line == wanted:
                has_wanted = True
        if has_wanted:
            pending.extend(locations)
    return sorted(pending)


@pytest.fixture
def project(tmp_path):
    """Create a tiny project skeleton with a scratch POT file."""
    src = tmp_path / "src"
    src.mkdir()
    return {
        "src": str(src),
        "pot": str(tmp_path / "messages.pot"),
    }


def test_header_comment_is_not_duplicated_on_repeated_extraction(project):
    """Repeated extraction must keep exactly one header comment block."""
    source = os.path.join(project["src"], "sample.py")
    _write(source, "from transx import tr\n" 'a = tr("Live Link")\n')

    for _ in range(3):
        _extract([source], project["pot"])

    content = _read(project["pot"])
    assert content.count(HEADER_MARKER) == 1, content


def test_header_comment_is_preserved_when_present(project):
    """A hand-edited header comment must survive a re-extraction verbatim."""
    source = os.path.join(project["src"], "sample.py")
    _write(source, "from transx import tr\n" 'a = tr("Hello")\n')

    _extract([source], project["pot"])

    content = _read(project["pot"])
    custom = "# My project translations.\n# Custom second line.\n"
    _write(project["pot"], custom + content.split("\n\n", 1)[1])

    _extract([source], project["pot"])
    content = _read(project["pot"])
    assert content.startswith(custom), content
    assert content.count(HEADER_MARKER) == 0, content


def test_repeated_extraction_does_not_duplicate_locations(project):
    """Extracting an unchanged source must not repeat ``#:`` references."""
    source = os.path.join(project["src"], "sample.py")
    _write(source, "from transx import tr\n" 'a = tr("Live Link")\n')

    for _ in range(3):
        _extract([source], project["pot"])

    locations = _location_lines(_read(project["pot"]))
    assert len(locations) == len(set(locations)), locations
    assert len(locations) == 1, locations


def test_extraction_is_idempotent(project):
    """Two consecutive runs over identical sources must produce identical POTs."""
    source = os.path.join(project["src"], "sample.py")
    _write(source, "from transx import tr\n" 'a = tr("Live Link")\n' 'b = tr("Other")\n')

    _extract([source], project["pot"])
    first = _read(project["pot"])
    _extract([source], project["pot"])
    second = _read(project["pot"])

    # The POT-Creation-Date stamp legitimately changes between runs.
    strip_date = lambda text: re.sub(r"POT-Creation-Date: .*", "POT-Creation-Date: X", text)  # noqa: E731
    assert strip_date(first) == strip_date(second)


def test_stale_locations_are_removed_when_string_moves(project):
    """Line numbers from previous runs must be dropped when a string moves."""
    source = os.path.join(project["src"], "sample.py")
    _write(
        source,
        "from transx import tr\n"
        "\n"
        'a = tr("Live Link")\n'  # line 3
        'b = tr("Other")\n'  # line 4
        'c = tr("Live Link")\n',
    )  # line 5

    _extract([source], project["pot"])
    before = _read(project["pot"])
    assert sorted(_locations_for(before, "Live Link")) == [
        "%s:3" % normalize_path(source),
        "%s:5" % normalize_path(source),
    ], before

    # "Live Link" now only lives on line 6.
    _write(
        source,
        "from transx import tr\n"
        "\n"
        "\n"
        "\n"
        'b = tr("Other")\n'  # line 5
        'c = tr("Live Link")\n',
    )  # line 6

    _extract([source], project["pot"])
    after = _read(project["pot"])

    assert _locations_for(after, "Live Link") == ["%s:6" % normalize_path(source)], after
    assert _locations_for(after, "Other") == ["%s:5" % normalize_path(source)], after


def test_removed_string_is_dropped_from_pot(project):
    """A string deleted from every scanned source must disappear from the POT."""
    source = os.path.join(project["src"], "sample.py")
    _write(source, "from transx import tr\n" 'a = tr("Gone")\n' 'b = tr("Stays")\n')

    _extract([source], project["pot"])
    assert 'msgid "Gone"' in _read(project["pot"])

    _write(source, "from transx import tr\n" 'b = tr("Stays")\n')

    _extract([source], project["pot"])
    content = _read(project["pot"])
    assert 'msgid "Gone"' not in content, content
    assert 'msgid "Stays"' in content, content


def test_locations_from_unscanned_files_are_preserved(project):
    """Partial extraction must not wipe references to files it did not scan."""
    first_source = os.path.join(project["src"], "first.py")
    second_source = os.path.join(project["src"], "second.py")
    _write(first_source, "from transx import tr\n" 'a = tr("Shared")\n')
    _write(second_source, "from transx import tr\n" 'b = tr("Shared")\n')

    _extract([first_source, second_source], project["pot"])
    content = _read(project["pot"])
    assert len(_locations_for(content, "Shared")) == 2, content

    # Drop the string from the file we are about to re-scan; the reference held
    # by the file that is NOT re-scanned must survive.
    _write(first_source, "from transx import tr\n" 'a = tr("Only here")\n')

    _extract([first_source], project["pot"])
    remaining = _locations_for(_read(project["pot"]), "Shared")
    assert remaining == ["%s:2" % normalize_path(second_source)], remaining


def test_message_locations_are_normalized():
    """Equivalent raw and normalized paths must collapse into one location."""
    raw = os.path.join("some", "nested", "file.py")
    message = POTFile().add("Hello", locations=[(raw, 10), (normalize_path(raw), 10)])
    assert message.locations == [(normalize_path(raw), 10)], message.locations


def test_message_add_location_normalizes_path():
    """``add_location`` must store the same form the reader produces."""
    raw = os.path.join("some", "nested", "file.py")
    message = POTFile().add("Hello")
    message.add_location(raw, 7)
    assert message.locations == [(normalize_path(raw), 7)], message.locations


def test_unreadable_source_file_keeps_its_entries(project):
    """A file in the scan set that cannot be read must not lose its entries.

    Regenerating a file's locations from scratch only makes sense once the file
    has actually been read. Resetting them first would make a transient read
    error look like "the strings are gone", and the stale sweep would then
    delete every entry unique to that file.
    """
    first_source = os.path.join(project["src"], "a.py")
    second_source = os.path.join(project["src"], "b.py")
    _write(first_source, "from transx import tr\n" 'a = tr("Alpha One")\n')
    _write(second_source, "from transx import tr\n" 'b = tr("Beta Two")\n')

    _extract([first_source, second_source], project["pot"])
    content = _read(project["pot"])
    assert 'msgid "Alpha One"' in content
    assert 'msgid "Beta Two"' in content

    # b.py stays in the scan set but can no longer be read.
    os.remove(second_source)

    _extract([first_source, second_source], project["pot"])
    content = _read(project["pot"])
    assert 'msgid "Alpha One"' in content
    assert 'msgid "Beta Two"' in content, "entries of an unreadable file must be kept, not pruned as stale"


def test_extractor_stores_normalized_locations(project):
    """Locations added by the extractor must use the normalized form.

    The reader normalizes paths, so the extractor must do the same - otherwise
    catalog entries end up holding a mixture of raw and normalized paths and
    equivalent references stop comparing equal.
    """
    source = os.path.join(project["src"], "sample.py")
    _write(source, "from transx import tr\n" 'a = tr("Live Link")\n')

    extractor = PotExtractor(source_files=[source], pot_file=project["pot"])
    extractor.extract_messages()

    message = extractor.catalog.translations["Live Link"]
    assert message.locations == [(normalize_path(source), 2)], message.locations


def test_reextraction_does_not_duplicate_locations_in_memory(project):
    """Re-extracting must not append a second, differently-spelled location.

    This walks the extractor path rather than Message's constructor, which is
    where a raw source path used to slip in next to the normalized one that was
    read back from disk.
    """
    source = os.path.join(project["src"], "sample.py")
    _write(source, "from transx import tr\n" 'a = tr("Live Link")\n')

    first = PotExtractor(source_files=[source], pot_file=project["pot"])
    first.extract_messages()
    first.save()

    second = PotExtractor(source_files=[source], pot_file=project["pot"])
    second.catalog.load()
    second.extract_messages()

    message = second.catalog.translations["Live Link"]
    assert message.locations == [(normalize_path(source), 2)], message.locations


def test_duplicate_source_file_is_scanned_once(project):
    """Listing the same file twice must not change the extraction result."""
    source = os.path.join(project["src"], "sample.py")
    _write(source, "from transx import tr\n" 'a = tr("Live Link")\n')

    _extract([source], project["pot"])
    single = _read(project["pot"])

    _extract([source, source], project["pot"])
    duplicated = _read(project["pot"])

    assert _location_lines(single) == _location_lines(duplicated)
