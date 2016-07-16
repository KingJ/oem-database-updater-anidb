from oem_updater.core.constants import TVDB_API_KEY
from oem_updater.models import Show, Season, SeasonMapping

from appdirs import AppDirs
import anidb
import logging
import os
import tvdb_api

log = logging.getLogger(__name__)


class AbsoluteMapper(object):
    constructed = False

    anidb = None
    anidb_cache = {}

    tvdb = None
    tvdb_cache = {}

    @classmethod
    def _construct(cls):
        if cls.constructed:
            return

        dirs = AppDirs('oem-updater', 'OpenEntityMap')

        # Ensure directories exist
        if not os.path.exists(dirs.user_cache_dir):
            os.makedirs(dirs.user_cache_dir)

        # Construct API clients
        cls.anidb = anidb.Anidb(cache=dirs.user_cache_dir, rate_limit=5)
        cls.tvdb = tvdb_api.Tvdb(apikey=TVDB_API_KEY, cache=dirs.user_cache_dir, use_requests=True)

        cls.constructed = True

    @classmethod
    def process(cls, collection, item):
        if not isinstance(item, Show):
            return False

        # Ensure clients are constructed
        cls._construct()

        # Retrieve default season
        default_season = item.parameters.get('default_season')

        if default_season != "a":
            return True

        # Fetch metadata
        try:
            anidb_metadata, tvdb_metadata = cls.fetch(item.identifiers)
        except Exception as ex:
            log.warn('Unable to fetch metadata for %r - %s', item.identifiers, ex)
            return False

        if not anidb_metadata or not tvdb_metadata:
            log.warn('Unable to fetch metadata for %r', item.identifiers)
            return False

        # Map episodes
        if collection.source == 'anidb' and collection.target == 'tvdb':
            cls.map_episodes_anidb(item, anidb_metadata, tvdb_metadata)
        elif collection.source == 'tvdb' and collection.target == 'anidb':
            cls.map_episodes_tvdb(item, anidb_metadata, tvdb_metadata)
        else:
            raise ValueError('Unsupported collection target: %r' % collection.target)

        return True

    @classmethod
    def map_episodes_anidb(cls, item, m_anidb, m_tvdb):
        # Parse episode offset
        episode_offset = None

        if 'episode_offset' in item.parameters:
            try:
                episode_offset = int(item.parameters['episode_offset'])
            except Exception:
                pass

        # Ensure season exists
        if '1' not in item.seasons:
            item.seasons['1'] = Season(item.collection, item, '1')

        # Construct season mappings
        for season_num, season in m_tvdb.items():
            if season_num < 1:
                continue

            season_num = str(season_num)

            # Retrieve absolute number
            if 1 not in season:
                continue

            absolute_num = season[1].get('absolute_number')

            if not absolute_num:
                continue

            absolute_num = int(absolute_num)

            if episode_offset:
                absolute_num -= episode_offset

            if absolute_num < 1:
                continue

            # Ensure episode exists in anidb
            if absolute_num not in m_anidb.episodes:
                continue

            # Construct season mapping
            episode_count = len([
                e for e in season.itervalues() if e['episodenumber'] != '0'
            ])

            item.seasons['1'].mappings.append(
                SeasonMapping(
                    item.collection, season_num,

                    start=absolute_num,
                    end=absolute_num + episode_count - 1,

                    offset=1 - absolute_num
                )
            )

        # Remove episode offset
        if 'episode_offset' in item.parameters:
            del item.parameters['episode_offset']

        # Update default season
        item.parameters['default_season'] = '1'

    @classmethod
    def map_episodes_tvdb(cls, item, m_anidb, m_tvdb):
        # Parse episode offset
        episode_offset = None

        if 'episode_offset' in item.parameters:
            try:
                episode_offset = int(item.parameters['episode_offset'])
            except Exception:
                pass

        # Construct seasons
        first_season = None

        for season_num, season in m_tvdb.items():
            if season_num < 1:
                continue

            season_num = str(season_num)

            # Retrieve absolute number
            if 1 not in season:
                continue

            absolute_num = season[1].get('absolute_number')

            if not absolute_num:
                continue

            absolute_num = int(absolute_num)

            if episode_offset:
                absolute_num -= episode_offset

            if absolute_num < 1:
                continue

            # Ensure episode exists in anidb
            if absolute_num not in m_anidb.episodes:
                continue

            # Set default season to first season
            if first_season is None:
                first_season = season_num

            # Construct season
            if season_num not in item.seasons:
                item.seasons[season_num] = Season(item.collection, item, season_num)

            item.seasons[season_num].parameters['default_season'] = 1
            item.seasons[season_num].parameters['episode_offset'] = absolute_num - 1

        # Remove episode offset
        if 'episode_offset' in item.parameters:
            del item.parameters['episode_offset']

        # Update default season
        item.parameters['default_season'] = first_season

    @classmethod
    def fetch(cls, identifiers):
        anidb_id = identifiers.get('anidb')
        tvdb_id = identifiers.get('tvdb')

        if not anidb_id or not tvdb_id:
            return

        # Fetch metadata
        return (
            cls.fetch_anidb(anidb_id),
            cls.fetch_tvdb(tvdb_id)
        )

    @classmethod
    def fetch_anidb(cls, anidb_id):
        # Check if metadata has been cached
        if anidb_id in cls.anidb_cache:
            return cls.anidb_cache[anidb_id]

        # Fetch anidb metadata
        try:
            anidb_metadata = cls.anidb.anime(anidb_id)
        except Exception as ex:
            log.warn('Unable to retrieve %r from anidb.net - %s', anidb_id, ex)
            cls.anidb_cache[anidb_id] = None
            return None

        if not anidb_metadata:
            log.warn('Unable to find %r on anidb.net', anidb_id)
            cls.anidb_cache[anidb_id] = None
            return None

        if anidb_metadata._xml.tag == "error":
            log.error('Error returned from anidb.net: %s', anidb_metadata._xml.text)
            exit(1)

        # Cache anidb metadata
        cls.anidb_cache[anidb_id] = anidb_metadata
        return anidb_metadata

    @classmethod
    def fetch_tvdb(cls, tvdb_id):
        try:
            tvdb_id = int(tvdb_id)
        except Exception as ex:
            raise ValueError('Invalid value provided for "tvdb_id" - %s' % ex)

        # Check if metadata has been cached
        if tvdb_id in cls.tvdb_cache:
            return cls.tvdb_cache[tvdb_id]

        # Fetch tvdb metadata
        try:
            tvdb_metadata = cls.tvdb[tvdb_id]
        except Exception as ex:
            log.warn('Unable to retrieve %r from thetvdb - %s', tvdb_id, ex)
            cls.tvdb_cache[tvdb_id] = None
            return None

        if not tvdb_metadata:
            log.warn('Unable to find %r on thetvdb.com', tvdb_id)
            cls.tvdb_cache[tvdb_id] = None
            return None

        # Cache tvdb metadata
        cls.tvdb_cache[tvdb_id] = tvdb_metadata
        return tvdb_metadata
