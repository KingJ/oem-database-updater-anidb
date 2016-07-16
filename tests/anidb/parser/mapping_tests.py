from tests.core.mock import MockCollection

from oem_core.models import Show
from oem_database_updater_anidb.parsers import Parser

from xml.etree import ElementTree


def test_absolute_season():
    collection = MockCollection('tvdb', 'anidb')

    current = Show(
        collection,
        identifiers={
            'anidb': 1530,
            'tvdb': 81472
        },
        names=set([
            'Dragon Ball Z'
        ]),

        default_season='a'
    )

    assert Parser.parse_mappings(current, collection, [
        ElementTree.fromstring('<mapping anidbseason="0" tvdbseason="0">;1-0;2-0;3-0;4-0;5-0;</mapping>')
    ]) is True


def test_invalid_show():
    collection = MockCollection('tvdb', 'anidb')

    current = Show(
        collection,
        identifiers={
            'anidb': 1490,
            'tvdb': 81341
        },
        names=set([
            'Jungle Taitei (1997)'
        ]),

        default_season='0'
    )

    assert Parser.parse_mappings(current, collection, [
        ElementTree.fromstring('<mapping anidbseason="1" tvdbseason="0">;1-0;2-0;3-0;</mapping>')
    ]) is False
