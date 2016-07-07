from oem_database_updater_anidb.parsers.core.absolute import AbsoluteMapper
from oem_framework.core.helpers import try_convert
from oem_framework.models import Item
from oem_database_updater_anidb.parsers.core.base import BaseParser

import logging

log = logging.getLogger(__name__)


class TVDbParser(BaseParser):
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

        # Retrieve TVDB identifier
        tvdb_id = node.attrib.get('tvdbid')

        if not tvdb_id or try_convert(tvdb_id, int) is None:
            log.warn('Item has an invalid TVDb identifier: %r (anidb_id: %r)', tvdb_id, anidb_id)
            return None

        # Construct item
        item = Item.construct(
            collection=collection,
            media=cls.get_collection_media(collection),

            identifiers=cls.parse_identifiers({
                'anidb': anidb_id,
                'tvdb': tvdb_id
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
