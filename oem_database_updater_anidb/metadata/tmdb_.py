from oem_updater.core.constants import TMDB_API_KEY

from requests import HTTPError
import tmdbsimple as tmdb

# Configure TMDb client
tmdb.API_KEY = TMDB_API_KEY


class TMDbMetadata(object):
    cache = {
        'movie': {},
        'show': {}
    }

    @classmethod
    def fetch(cls, tmdb_id, media):
        # Return item from cache (if available)
        if tmdb_id in cls.cache[media]:
            return cls.cache[media][tmdb_id]

        # Fetch item via TMDb API
        if media == 'movie':
            item = tmdb.Movies(tmdb_id)
        elif media == 'show':
            item = tmdb.TV(tmdb_id)
        else:
            raise NotImplementedError('Unsupported media type: %r' % media)

        try:
            item.info()
        except HTTPError:
            item = None

        # Store item in cache
        cls.cache[media][tmdb_id] = item
        return item
