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
            return

        # Retrieve episode offset (and cast to integer)
        episode_offset = try_convert(node.attrib.get('episodeoffset'), int)

        # Retrieve AniDB identifier
        anidb_id = cls.get_anidb_id(node)

        if anidb_id is None:
            log.warn('Item has an invalid AniDB identifier: %r ', anidb_id)
            return

        # Retrieve IMDB identifier
        imdb_ids = node.attrib.get('imdbid', '').split(',')

        if not cls._validate_identifier(imdb_ids):
            return

        # Parse items
        for x, imdb_id in enumerate(imdb_ids):
            if imdb_id == 'unknown':
                continue

            # Determine item episode offset
            i_episode_offset = episode_offset

            if len(imdb_ids) > 1:
                i_episode_offset = (episode_offset or 0) + x

            if i_episode_offset is not None:
                if i_episode_offset != 0:
                    i_episode_offset = str(i_episode_offset)
                else:
                    i_episode_offset = None

            # Construct item
            item = cls.parse_one(
                collection, node,
                anidb_id, imdb_id,
                default_season,
                i_episode_offset,
                use_absolute_mapper=use_absolute_mapper
            )

            if not item:
                continue

            yield item

    @classmethod
    def parse_one(cls, collection, node, anidb_id, imdb_id, default_season, episode_offset, use_absolute_mapper=True):
        item = Item.construct(
            collection=collection,
            media=cls.get_collection_media(collection),

            identifiers=cls.parse_identifiers({
                'anidb': anidb_id,
                'imdb': imdb_id
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
