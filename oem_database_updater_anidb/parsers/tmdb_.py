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
            return None

        # Retrieve AniDB identifier
        anidb_id = cls.get_anidb_id(node)

        if anidb_id is None:
            log.warn('Item has an invalid AniDB identifier: %r ', anidb_id)
            return None

        # Retrieve TMDb identifier
        tmdb_id = node.attrib.get('tmdbid')

        if not tmdb_id or try_convert(tmdb_id, int) is None:
            log.warn('Item has an invalid TMDb identifier: %r (anidb_id: %r)', tmdb_id, anidb_id)
            return None

        # Construct item
        item = Item.construct(
            collection=collection,
            media=cls.get_collection_media(collection),

            identifiers=cls.parse_identifiers({
                'anidb': anidb_id,
                'tmdb': tmdb_id
            }),
            names={},

            default_season=default_season,
            episode_offset=node.attrib.get('episodeoffset')
        )

        # Parse names
        cls.parse_names(item, collection, node)

        # Fetch AniDb metadata
        anidb_metadata = AniDbMetadata.fetch(anidb_id)

        if not anidb_metadata:
            log.error('Unable to fetch metadata from AniDb')
            exit(1)

        # Fetch TMDb metadata
        tmdb_metadata = TMDbMetadata.fetch(tmdb_id, item.media)

        if not tmdb_metadata:
            log.error('Unable to fetch metadata from TMDb')
            exit(1)

        # Verify item against TMDb
        if not cls.verify(item, anidb_metadata, tmdb_metadata):
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
    def verify(cls, item, anidb_metadata, tmdb_metadata):
        if item.media == 'movie':
            return cls.verify_movie(item, anidb_metadata, tmdb_metadata)
        elif item.media == 'show':
            return cls.verify_show(item, anidb_metadata, tmdb_metadata)

        return False

    @classmethod
    def verify_movie(cls, item, anidb_metadata, tmdb_metadata):
        return False

    @classmethod
    def verify_show(cls, item, anidb_metadata, tmdb_metadata):
        return False
