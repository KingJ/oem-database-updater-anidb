from oem_framework.core.helpers import try_convert
from oem_framework.models import Item
from oem_database_updater_anidb.parsers.core.absolute import AbsoluteMapper
from oem_database_updater_anidb.parsers.core.base import BaseParser

import logging

IGNORE_IDENTIFIERS = [
    'hentai',
    'movie',
    'music video',
    'other',
    'OVA',
    'tv special',
    'tvspecial',
    'unknown',
    'web'
]

log = logging.getLogger(__name__)


class TVDbParser(BaseParser):
    @classmethod
    def parse(cls, collection, node, use_absolute_mapper=True):
        # Retrieve default season
        default_season = node.attrib.get('defaulttvdbseason')

        if default_season is None:
            return

        # Retrieve episode offset (and cast to integer)
        episode_offset = try_convert(node.attrib.get('episodeoffset'), int, 0)

        # Retrieve AniDB identifier
        anidb_id = cls.get_anidb_id(node)

        if anidb_id is None:
            log.warn('Item has an invalid AniDB identifier: %r ', anidb_id)
            return

        # Retrieve TVDB identifier
        tvdb_ids = node.attrib.get('tvdbid', '').split(',')

        if not cls._validate_identifier(tvdb_ids):
            return

        # Parse items
        for x, tvdb_id in enumerate(tvdb_ids):
            if tvdb_id == 'unknown':
                continue

            # Determine item episode offset
            i_episode_offset = episode_offset

            if len(tvdb_ids) > 1:
                i_episode_offset = (episode_offset or 0) + x

            if i_episode_offset is not None:
                if i_episode_offset != 0:
                    i_episode_offset = str(i_episode_offset)
                else:
                    i_episode_offset = None

            # Construct item
            item = cls.parse_one(
                collection, node,
                anidb_id, tvdb_id,
                default_season,
                i_episode_offset,
                use_absolute_mapper=use_absolute_mapper
            )

            if not item:
                continue

            yield item

    @classmethod
    def parse_one(cls, collection, node, anidb_id, tvdb_id, default_season, episode_offset, use_absolute_mapper=True):
        item = Item.construct(
            collection=collection,
            media=cls.get_collection_media(collection),

            identifiers=cls.parse_identifiers({
                'anidb': anidb_id,
                'tvdb': tvdb_id
            }),
            names={},

            default_season=default_season,
            episode_offset=episode_offset
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
    def _validate_identifier(tvdb_ids):
        if not tvdb_ids:
            log.warn('Item has an invalid TVDb identifier: %r', tvdb_ids)
            return False

        valid = False

        for tvdb_id in tvdb_ids:
            if tvdb_id in IGNORE_IDENTIFIERS:
                continue

            if not tvdb_id:
                log.warn('Item has an invalid TVDb identifier: %r', tvdb_id)
                continue

            if try_convert(tvdb_id, int) is None:
                log.warn('Item has an invalid TVDb identifier: %r', tvdb_id)
                return None

            valid = True

        return valid
