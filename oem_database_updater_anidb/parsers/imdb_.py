from oem_database_updater_anidb.parsers.core.absolute import AbsoluteMapper
from oem_framework.core.helpers import try_convert
from oem_framework.models import Item
from oem_database_updater_anidb.parsers.core.base import BaseParser

import logging

log = logging.getLogger(__name__)


class IMDbParser(BaseParser):
    @classmethod
    def parse(cls, collection, node, use_absolute_mapper=True):
        # Retrieve default season
        default_season = node.attrib.get('defaulttvdbseason')

        if default_season is None:
            return None

        # Retrieve AniDB identifier
        anidb_id = cls.get_anidb_id(node)

        if anidb_id is None:
            log.warn('Item has an invalid AniDB identifier: %r ', anidb_id)
            return None

        # Retrieve IMDB identifier
        imdb_ids = node.attrib.get('imdbid', '').split(',')

        if not cls._validate_identifier(imdb_ids):
            return None

        # Construct item
        item = Item.construct(
            collection=collection,
            media=cls.get_collection_media(collection),

            identifiers=cls.parse_identifiers({
                'anidb': anidb_id,
                'imdb': imdb_ids
            }),
            names={},

            default_season=default_season,
            episode_offset=node.attrib.get('episodeoffset')
        )

        # Parse names
        cls.parse_names(item, collection, node)

        # Parse mappings
        mappings = list(node.findall('mapping-list//mapping'))

        if item.media == 'show' and not cls.parse_mappings(item, collection, mappings):
            return None

        # Parse supplemental
        cls.parse_supplemental(item, node)

        # Convert absolute mappings (if enabled)
        if use_absolute_mapper:
            AbsoluteMapper.process(collection, item)

        return item

    @staticmethod
    def _validate_identifier(imdb_ids):
        if not imdb_ids:
            log.warn('Item has an invalid IMDB identifier: %r', imdb_ids)
            return False

        valid = False

        for imdb_id in imdb_ids:
            if imdb_id == 'unknown':
                continue

            if not imdb_id:
                log.warn('Item has an invalid IMDB identifier: %r', imdb_id)
                continue

            if not imdb_id.startswith('tt') or try_convert(imdb_id[2:], int) is None:
                log.warn('Item has an invalid IMDB identifier: %r', imdb_id)
                continue

            valid = True

        return valid
