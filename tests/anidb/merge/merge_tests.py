from oem_core.models import SeasonMapping
from oem_database_updater_anidb.parsers import Parser
from tests.core.mock import MockCollection

from xml.etree import ElementTree
import os
import six

BASE_DIR = os.path.dirname(__file__)


def merge_items(collection, filename):
    nodes = ElementTree.iterparse(os.path.join(BASE_DIR, 'fixtures', filename))

    current = None

    for _, node in nodes:
        if node.tag != 'anime':
            continue

        # Parse item
        item = Parser.parse(collection, node, use_absolute_mapper=False)

        if item is None:
            continue

        # Update `current` item
        if current is None:
            current = item
        else:
            current.add(item, 'tvdb')

    return current


def test_black_lagoon():
    collection = MockCollection('tvdb', 'anidb')
    current = merge_items(collection, 'black-lagoon.xml')

    # Validate result
    assert current.identifiers == {'tvdb': '79604'}
    assert current.names == {}
    assert set(current.seasons.keys()) == set(['0', '1'])

    # - Season 0
    assert current.seasons['0'].identifiers == {}
    assert len(current.seasons['0'].names) == 0
    assert set(current.seasons['0'].episodes.keys()) == set(['5', '6', '7', '8'])

    assert current.seasons['0'].episodes['5'].identifiers == {'anidb': '4597'}
    assert current.seasons['0'].episodes['5'].names == {'4597': set(['Black Lagoon: The Second Barrage'])}
    assert current.seasons['0'].episodes['6'].identifiers == {'anidb': '4597'}
    assert current.seasons['0'].episodes['6'].names == {'4597': set(['Black Lagoon: The Second Barrage'])}
    assert current.seasons['0'].episodes['7'].identifiers == {'anidb': '4597'}
    assert current.seasons['0'].episodes['7'].names == {'4597': set(['Black Lagoon: The Second Barrage'])}
    assert current.seasons['0'].episodes['8'].identifiers == {'anidb': '6645'}
    assert current.seasons['0'].episodes['8'].names == {'6645': set(['Black Lagoon: Roberta\'s Blood Trail'])}

    assert len(current.seasons['0'].mappings) == 1
    assert current.seasons['0'].mappings[0] == SeasonMapping(
        collection, '0', 13, 17, -12,
        identifiers={'anidb': '6645'},
        names=set(['Black Lagoon: Roberta\'s Blood Trail'])
    )

    # - Season 1
    assert current.seasons['1'].identifiers == {'anidb': '3395'}
    assert current.seasons['1'].names == {'3395': set(['Black Lagoon'])}
    assert set(current.seasons['1'].episodes.keys()) == set(['13'])

    assert current.seasons['1'].episodes['13'].identifiers == {'anidb': '4597'}
    assert current.seasons['1'].episodes['13'].names == {'4597': set(['Black Lagoon: The Second Barrage'])}

    # Validate dictionary output
    data = current.to_dict()

    assert data['seasons']['0']['mappings'][0]['names'] == ['Black Lagoon: Roberta\'s Blood Trail']


def test_cobra_the_animation():
    collection = MockCollection('tvdb', 'anidb')
    current = merge_items(collection, 'cobra-the-animation.xml')

    # Validate result
    assert current.identifiers == {'tvdb': '137151'}
    assert current.names == {}
    assert set(current.seasons.keys()) == set(['0', '1'])

    # - Season 0
    assert current.seasons['0'].identifiers == {'anidb': '5894'}
    assert current.seasons['0'].names == {'5894': set(['Cobra The Animation: The Psychogun'])}
    assert set(current.seasons['0'].episodes.keys()) == set(['5', '6'])

    assert current.seasons['0'].episodes['5'].identifiers == {'anidb': '6392'}
    assert current.seasons['0'].episodes['5'].names == {'6392': set(['Cobra The Animation: Time Drive'])}
    assert current.seasons['0'].episodes['6'].identifiers == {'anidb': '6392'}
    assert current.seasons['0'].episodes['6'].names == {'6392': set(['Cobra The Animation: Time Drive'])}

    # - Season 1
    assert current.seasons['1'].identifiers == {'anidb': set(['6392', '6494'])}
    assert current.seasons['1'].names == {'6392': set(['Cobra The Animation: Time Drive']), '6494': set(['Cobra The Animation'])}
    assert len(current.seasons['1'].episodes.keys()) == 0


def test_dragon_ball_z():
    collection = MockCollection('tvdb', 'anidb')
    current = merge_items(collection, 'dragon-ball-z.xml')

    # Validate result
    assert current.identifiers == {'tvdb': '81472'}
    assert current.names == {}
    assert set(current.seasons.keys()) == set(['0', 'a'])

    #  - Season 0
    assert current.seasons['0'].identifiers == {'anidb': '1043'}
    assert current.seasons['0'].names == {'1043': set(['Dragon Ball Z (1989)'])}
    assert set(current.seasons['0'].episodes.keys()) == set([
        '2', '3', '4', '5', '6', '7', '8', '9',
        '10', '11', '12', '13', '14', '15', '16', '17', '18',
        '20', '21', '22'
    ])

    #  - Absolute
    assert current.seasons['a'].identifiers == {'anidb': '1530'}
    assert current.seasons['a'].names == {'1530': set(['Dragon Ball Z'])}
    assert len(current.seasons['a'].episodes.keys()) == 0


def test_gall_force():
    collection = MockCollection('tvdb', 'anidb')
    current = merge_items(collection, 'gall-force.xml')

    # Validate result
    assert current.identifiers == {'tvdb': '138691'}
    assert current.names == {}
    assert set(current.seasons.keys()) == set(['0', '1'])

    # - Season 0
    assert current.seasons['0'].identifiers == {'anidb': '2891'}
    assert current.seasons['0'].names == {'2891': set(['Scramble Wars: Tsuppashire! Genom Trophy Rally'])}
    assert set(current.seasons['0'].episodes.keys()) == set(['2'])

    # - Season 1
    assert current.seasons['1'].identifiers == {'anidb': '760'}
    assert current.seasons['1'].names == {'760': set(['Gall Force: Eternal Story'])}
    assert set(current.seasons['1'].episodes.keys()) == set(str(x) for x in six.moves.xrange(2, 14))

    assert current.seasons['1'].episodes['5'].identifiers == {'anidb': '2115'}
    assert current.seasons['1'].episodes['5'].names == {'2115': set(['Gall Force: Chikyuu Shou'])}
