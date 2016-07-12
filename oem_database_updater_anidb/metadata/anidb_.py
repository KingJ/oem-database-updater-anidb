from appdirs import AppDirs
import anidb
import logging
import os

log = logging.getLogger(__name__)


class AniDbMetadata(object):
    constructed = False

    client = None
    cache = {}

    @classmethod
    def _construct(cls):
        if cls.constructed:
            return

        dirs = AppDirs('oem-updater', 'OpenEntityMap')

        # Ensure directories exist
        if not os.path.exists(dirs.user_cache_dir):
            os.makedirs(dirs.user_cache_dir)

        # Construct client
        cls.client = anidb.Anidb(cache=dirs.user_cache_dir, rate_limit=5)

        # Mark as constructed
        cls.constructed = True

    @classmethod
    def fetch(cls, anidb_id):
        # Ensure client is constructed
        cls._construct()

        # Check if metadata has been cached
        if anidb_id in cls.cache:
            return cls.cache[anidb_id]

        # Fetch anidb metadata
        try:
            item = cls.client.anime(anidb_id)
        except Exception as ex:
            log.warn('Unable to retrieve %r from anidb.net - %s', anidb_id, ex, exc_info=True)
            cls.cache[anidb_id] = None
            return None

        if not item:
            log.warn('Unable to find %r on anidb.net', anidb_id)
            cls.cache[anidb_id] = None
            return None

        if item._xml.tag == "error":
            log.error('Error returned from anidb.net: %s', item._xml.text)
            exit(1)

        # Cache anidb metadata
        cls.cache[anidb_id] = item
        return item
