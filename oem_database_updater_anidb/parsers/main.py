from oem_framework.core.elapsed import Elapsed
from oem_framework.core.helpers import try_convert
from oem_updater.models import Item
from oem_database_updater_anidb.parsers.core.absolute import AbsoluteMapper

import logging


COLLECTION_TMDB_KEYS = [
    ('tmdb', 'movie'),
    ('tmdb', 'show')
]

log = logging.getLogger(__name__)


class LegacyParser(object):
    __version__ = 0x00

    @classmethod
    @Elapsed.track
    def parse_item(cls, collection, node, use_absolute_mapper=True):
        # Retrieve default season
        default_season = node.attrib.get('defaulttvdbseason')

        if default_season is None:
            return None

        # Construct item
        item = Item.construct(
            collection=collection,
            media=cls.get_collection_media(collection),

            identifiers={'anidb': cls.get_anidb_id(node)},
            names={},

            default_season=default_season,
            episode_offset=node.attrib.get('episodeoffset')
        )

        imdb_id = node.attrib.get('imdbid')
        tmdb_id = node.attrib.get('tmdbid')
        tvdb_id = node.attrib.get('tvdbid')
        mappings = list(node.findall('mapping-list//mapping'))
        supplemental = node.find('supplemental-info')

        # Parse identifiers
        if collection.source == 'imdb' or collection.target == 'imdb':
            if imdb_id and imdb_id.startswith('tt'):
                item.identifiers['imdb'] = imdb_id.split(',')
            else:
                # Invalid item
                return None
        elif collection.source in COLLECTION_TMDB_KEYS or collection.target in COLLECTION_TMDB_KEYS:
            if tmdb_id and try_convert(tmdb_id, int) is not None:
                item.identifiers['tmdb'] = tmdb_id.split(',')
            else:
                # Invalid item
                return None
        elif collection.source == 'tvdb' or collection.target == 'tvdb':
            if tvdb_id and try_convert(tvdb_id, int) is not None:
                item.identifiers['tvdb'] = tvdb_id.split(',')
            else:
                # Invalid item
                return None
        else:
            raise ValueError('Unknown service for: %r' % collection)

        for service, keys in item.identifiers.items():
            if type(keys) is not list:
                continue

            # Filter out "unknown" identifiers
            item.identifiers[service] = [
                key for key in item.identifiers[service]
                if key != 'unknown'
            ]

            # Collapse lists with only 1 key
            if len(keys) < 2:
                item.identifiers[service] = keys[0]

        # Parse names
        target_key = item.identifiers[collection.target]

        if type(target_key) is list:
            for key in target_key:
                item.names[key] = set([node.find('name').text])
        else:
            item.names[target_key] = set([node.find('name').text])

        # Verify item identifiers
        # if not cls.verify(item):
        #     return None

        # Parse mappings
        if item.media == 'show' and not cls.parse_mappings(collection, item, mappings):
            return None

        # Add supplemental
        if supplemental is not None:
            item.supplemental = {}

            # TODO store all supplemental nodes
            for key in ['studio']:
                node = supplemental.find(key)

                if node is not None:
                    item.supplemental[key] = node.text

        # Convert absolute mappings (if enabled)
        if use_absolute_mapper:
            AbsoluteMapper.process(collection, item)

        return item

    @classmethod
    def verify(cls, item):
        if 'tmdb' in item.identifiers:
            return cls.verify_tmdb(item)

        return True

    @classmethod
    def verify_tmdb(cls, item):
        if item.media == 'movie':
            metadata = tmdb.Movies(item.identifiers['tmdb'])
            metadata.info()
        elif item.media == 'show':
            metadata = tmdb.TV(item.identifiers['tmdb'])
            metadata.info()
        else:
            return False

        # Retrieve metadata title
        metadata_title = None

        if isinstance(metadata, tmdb.Movies):
            metadata_title = metadata.title
        elif isinstance(metadata, tmdb.TV):
            metadata_title = metadata.name
        else:
            return False

        # Verify names match
        names_match = False

        for _, names in item.names.items():
            for name in names:
                if name == metadata_title:
                    names_match = True

        if not names_match:
            log.warn('Item doesn\'t match TMDb metadata (item.names: %r, title: %r)', item.names, metadata_title)
            return False

        return True
