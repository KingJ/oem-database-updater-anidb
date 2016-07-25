from oem_database_updater_anidb.constants import COLLECTION_KEYS_TMDB
from oem_database_updater_anidb.metadata.anidb_ import AniDbMetadata
from oem_database_updater_anidb.metadata.tmdb_ import TMDbMetadata
from oem_database_updater_anidb.parsers.core.absolute import AbsoluteMapper
from oem_framework.core.helpers import try_convert
from oem_framework.models import Item
from oem_database_updater_anidb.parsers.core.base import BaseParser

import logging

log = logging.getLogger(__name__)


class TMDbParser(BaseParser):
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

        # Retrieve TMDb identifier
        media, tmdb_ids = cls._get_tmdb_identifier(node)

        if not media or media != cls.get_collection_media(collection):
            return

        if not cls._validate_identifier(tmdb_ids):
            return

        # Parse items
        for x, tmdb_id in enumerate(tmdb_ids):
            if tmdb_id == 'unknown':
                continue

            # Determine item episode offset
            i_episode_offset = episode_offset

            if len(tmdb_ids) > 1:
                i_episode_offset = (episode_offset or 0) + x

            if i_episode_offset is not None:
                if i_episode_offset != 0:
                    i_episode_offset = str(i_episode_offset)
                else:
                    i_episode_offset = None

            # Construct item
            item = cls.parse_one(
                collection, node, media,
                anidb_id, tmdb_id,
                default_season,
                i_episode_offset,
                use_absolute_mapper=use_absolute_mapper
            )

            if not item:
                continue

            yield item

    @classmethod
    def parse_one(cls, collection, node, media, anidb_id, tmdb_id, default_season, episode_offset,
                  use_absolute_mapper=True):

        # Retrieve identifier key
        if collection.source in COLLECTION_KEYS_TMDB:
            identifier_key = collection.source
        elif collection.target in COLLECTION_KEYS_TMDB:
            identifier_key = collection.target
        else:
            log.warn('Unable to find identifier key')
            return None

        # Construct item
        item = Item.construct(
            collection=collection,
            media=media,

            identifiers=cls.parse_identifiers({
                'anidb': anidb_id,
                identifier_key: tmdb_id
            }),
            names={},

            default_season=default_season,
            episode_offset=episode_offset
        )

        # Parse names
        cls.parse_names(item, collection, node)

        # Fetch AniDb metadata
        metadata_anidb = AniDbMetadata.fetch(anidb_id)

        if not metadata_anidb:
            log.error('Unable to fetch %r from AniDb', anidb_id)
            return None

        # Fetch TMDb metadata
        metadata_tmdb = TMDbMetadata.fetch(tmdb_id, item.media)

        if not metadata_tmdb:
            log.error('Unable to fetch %r from TMDb', tmdb_id)
            return None

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

    @classmethod
    def _get_tmdb_identifier(cls, node):
        if 'tmdbmid' in node.attrib:
            if node.attrib.get('tmdbid') != node.attrib['tmdbmid']:
                log.warn('Item %r "tmdbid" should be set to the same value as "tmdbmid"', node.attrib.get('anidbid'))

            return 'movie', node.attrib['tmdbmid'].split(',')

        if 'tmdbsid' in node.attrib:
            return 'show', node.attrib['tmdbsid'].split(',')

        if 'tmdbid' in node.attrib:
            log.warn('Item %r is missing the new-style tmdb identifier', node.attrib.get('anidbid'))
            return None, None

        return None, None

    @staticmethod
    def _validate_identifier(tmdb_ids):
        if not tmdb_ids:
            log.warn('Item has an invalid TMDb identifier: %r', tmdb_ids)
            return False

        valid = False

        for tmdb_id in tmdb_ids:
            if tmdb_id == 'unknown':
                continue

            if not tmdb_id:
                log.warn('Item has an invalid TMDb identifier: %r', tmdb_id)
                continue

            if try_convert(tmdb_id, int) is None:
                log.warn('Item has an invalid TMDb identifier: %r', tmdb_id)
                return None

            valid = True

        return valid
