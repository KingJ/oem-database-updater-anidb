from oem_updater.models import Season, SeasonMapping, Episode, EpisodeMapping, Range
from oem_database_updater_anidb.constants import COLLECTIONS_MOVIES, COLLECTIONS_SHOWS

import re


class BaseParser(object):
    @classmethod
    def parse(cls, collection, node, use_absolute_mapper=True):
        raise NotImplementedError

    @classmethod
    def get_anidb_id(cls, node):
        anidb_id = node.attrib.get('anidbid').split(',')

        if len(anidb_id) == 1:
            anidb_id = anidb_id[0]
        elif len(anidb_id) < 1:
            anidb_id = None

        return anidb_id

    @classmethod
    def get_collection_media(cls, collection):
        key = (collection.source, collection.target)

        if key in COLLECTIONS_MOVIES:
            return 'movie'

        if key in COLLECTIONS_SHOWS:
            return 'show'

        raise Exception('Unknown collection media: %r' % collection)

    @classmethod
    def parse_names(cls, item, collection, node):
        target_key = item.identifiers[collection.target]

        if type(target_key) is list:
            for key in target_key:
                item.names[key] = set([node.find('name').text])
        else:
            item.names[target_key] = set([node.find('name').text])

    @classmethod
    def parse_supplemental(cls, item, node):
        supplemental = node.find('supplemental-info')

        if supplemental is None:
            return

        item.supplemental = {}

        # TODO store all supplemental nodes
        for key in ['studio']:
            node = supplemental.find(key)

            if node is not None:
                item.supplemental[key] = node.text

    @classmethod
    def parse_identifiers(cls, identifiers):
        for service, keys in identifiers.items():
            if type(keys) is not list:
                continue

            # Filter out "unknown" identifiers
            identifiers[service] = [
                key for key in identifiers[service]
                if key != 'unknown'
            ]

            # Collapse lists with only 1 key
            if len(keys) < 2:
                identifiers[service] = keys[0]

        return identifiers

    @classmethod
    def parse_mappings(cls, item, collection, mappings):
        if not mappings:
            return True

        # Parse mappings
        error = None

        for mapping in mappings:
            source_season = mapping.attrib.get(collection.source + 'season')
            target_season = mapping.attrib.get(collection.target + 'season')

            # Parse mapping
            if mapping.text:
                if cls.parse_mappings_episode(collection, item, mapping, (source_season, target_season)):
                    error = False
                elif error is None and item.parameters.get('default_season') == source_season:
                    error = True
            else:
                cls.parse_mappings_season(collection, item, mapping, (source_season, target_season))

        # Check for parsing error
        if error:
            return False

        # Successfully parsed item
        return True

    @classmethod
    def parse_mappings_episode(cls, collection, item, mapping, identifier):
        source_season, target_season = identifier

        # Parse episodes
        episodes = list(cls.parse_episodes(collection, mapping.text))

        if not episodes:
            return False

        # Ensure season exists
        if source_season not in item.seasons:
            item.seasons[source_season] = Season(collection, item, source_season)

        # Construct episodes
        for (s_number, s_start, s_end), (t_number, t_start, t_end) in episodes:
            # Ensure episode exists
            if s_number not in item.seasons[source_season].episodes:
                # Construct episode
                item.seasons[source_season].episodes[s_number] = Episode(
                    collection,
                    item.seasons[source_season],

                    number=s_number
                )

            # Construct episode mapping
            item.seasons[source_season].episodes[s_number].mappings.append(
                EpisodeMapping(
                    collection,
                    item.seasons[source_season].episodes[s_number],

                    season=target_season,
                    number=t_number,

                    timeline={
                        'source': Range(collection, t_start, t_end),
                        'target': Range(collection, s_start, s_end)
                    }
                )
            )

        return True

    @classmethod
    def parse_mappings_season(cls, collection, item, mapping, identifier):
        source_season, target_season = identifier

        # Retrieve parameters, convert to integers
        start = int(mapping.attrib.get('start'))
        end = int(mapping.attrib.get('end'))

        offset = int(mapping.attrib.get('offset'))

        # Reverse season mappings for non-anidb source collections
        if collection.source != 'anidb':
            start += offset
            end += offset

            offset = -offset

        # Ensure season exists
        if source_season not in item.seasons:
            item.seasons[source_season] = Season(collection, item, source_season)

        # Construct season mapping
        item.seasons[source_season].mappings.append(
            SeasonMapping(
                collection, target_season,

                start=start,
                end=end,

                offset=offset
            )
        )

        return True

    @classmethod
    def parse_episodes(cls, collection, value):
        episodes = [
            tuple(episode.split('-'))
            for episode in re.split(r"[;:]", value)
            if episode
        ]

        for item in episodes:
            if len(item) != 2:
                continue

            anidb_numbers, other_numbers = item

            # Select source + target numbers
            if collection.source == 'anidb':
                source_numbers, target_numbers = anidb_numbers, other_numbers
            else:
                source_numbers, target_numbers = other_numbers, anidb_numbers

            # Split numbers
            source_numbers = source_numbers.split('+')
            source_count = len(source_numbers)

            target_numbers = target_numbers.split('+')
            target_count = len(target_numbers)

            # Iterate over source episodes
            for source_index, source_number in enumerate(source_numbers):
                # Ensure source number is defined
                if source_number == '0' or source_number == '99':
                    continue

                # Calculate source timeline range
                source_start = int(round((float(source_index) / source_count) * 100, 0))
                source_end = int(round((float(source_index + 1) / source_count) * 100, 0))

                # Iterate over target episodes
                for target_index, target_number in enumerate(target_numbers):
                    # Calculate target timeline range
                    target_start = int(round((float(target_index) / target_count) * 100, 0))
                    target_end = int(round((float(target_index + 1) / target_count) * 100, 0))

                    # Yield episode
                    yield (
                        source_number,
                        source_start,
                        source_end
                    ), (
                        target_number,
                        target_start,
                        target_end
                    )
