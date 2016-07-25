from oem_database_updater_anidb.constants import COLLECTION_KEYS_IMDB, COLLECTION_KEYS_TMDB, COLLECTION_KEYS_TVDB
from oem_database_updater_anidb.parsers.core.base import BaseParser
from oem_database_updater_anidb.parsers.imdb_ import IMDbParser
from oem_database_updater_anidb.parsers.tmdb_ import TMDbParser
from oem_database_updater_anidb.parsers.tvdb_ import TVDbParser
from oem_framework.core.elapsed import Elapsed


class Parser(BaseParser):
    @classmethod
    @Elapsed.track
    def parse(cls, collection, node, use_absolute_mapper=True):
        parser = cls.get_parser(collection, node)

        if not parser:
            return []

        return parser.parse(
            collection, node,
            use_absolute_mapper=use_absolute_mapper
        )

    @staticmethod
    def get_parser(collection, node):
        source = collection.source
        target = collection.target

        if (source in COLLECTION_KEYS_IMDB or target in COLLECTION_KEYS_IMDB) and 'imdbid' in node.attrib:
            return IMDbParser

        if (source in COLLECTION_KEYS_TMDB or target in COLLECTION_KEYS_TMDB) and (
            'tmdbid' in node.attrib or
            'tmdbmid' in node.attrib or
            'tmdbsid' in node.attrib
        ):
            return TMDbParser

        if (source in COLLECTION_KEYS_TVDB or target in COLLECTION_KEYS_TVDB) and 'tvdbid' in node.attrib:
            return TVDbParser

        return None
