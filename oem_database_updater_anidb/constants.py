COLLECTIONS = [
    # IMDb
    ('anidb', 'imdb'),

    # TMDb
    ('anidb', 'tmdb:movie'),
    ('anidb', 'tmdb:show'),

    # TheTVDb
    ('anidb', 'tvdb')
]

#
# Media
#

COLLECTIONS_MOVIES = [
    # IMDb
    ('anidb', 'imdb'),
    ('imdb', 'anidb'),

    # TMDb
    ('anidb', 'tmdb:movie'),
    ('tmdb:movie', 'anidb')
]

COLLECTIONS_SHOWS = [
    # TMDb
    ('anidb', 'tmdb:show'),
    ('tmdb:show', 'anidb'),

    # TheTVDb
    ('anidb', 'tvdb'),
    ('tvdb', 'anidb')
]

#
# Services
#

COLLECTION_KEYS_IMDB = [
    'imdb'
]

COLLECTION_KEYS_TMDB = [
    'tmdb:movie',
    'tmdb:show'
]

COLLECTION_KEYS_TVDB = [
    'tvdb'
]
