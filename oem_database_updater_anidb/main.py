from oem_framework.core.elapsed import Elapsed
from oem_updater.core.sources.base import Source
from oem_database_updater_anidb.constants import COLLECTIONS
from oem_database_updater_anidb.parsers import Parser

from xml.etree import ElementTree
import logging
import os
import sys

log = logging.getLogger(__name__)


class AniDB(Source):
    __key__ = 'anidb'
    __collections__ = COLLECTIONS

    __parameters__ = [
        {'name': 'source'}
    ]

    def __init__(self, collection, kwargs):
        super(AniDB, self).__init__(collection, kwargs)

        self.seen = {}
        self.updated = {}

    def run(self):
        # Retrieve source path
        source_path = self.param('source')

        if not source_path:
            log.error('Invalid value provided for the "--anidb-source" parameter')
            return False

        # Ensure `source_path` exists
        if not os.path.exists(source_path):
            log.error('Path %r doesn\'t exist', source_path)
            return False

        # Process items
        if not self.process(source_path):
            return False

        return True

    def process(self, source_path):
        progress = self.param('progress')

        # Process items
        count_total = 0
        count_updated = 0

        for _, item in ElementTree.iterparse(source_path):
            if item.tag != 'anime':
                continue

            if progress:
                sys.stdout.write('\r%s - (%05d/%05d)' % (self.collection, count_updated, count_total))
                sys.stdout.flush()

            count_total += 1

            # Process item
            success, updated = self.process_one(item)

            if not success:
                continue

            if updated:
                count_updated += 1

        if progress:
            sys.stdout.write('\n')

        return True

    @Elapsed.track
    def process_one(self, node):
        updated = False

        for item in Parser.parse(self.collection, node):
            # Update item (if not already stored)
            i_success, i_updated = self.update(self.collection.source, self.collection.target, node, item)

            # Update state
            updated |= i_updated

            if not i_success:
                # Error detected, stop processing of item
                return False, updated

        # Invalid item for collection
        return True, updated

    @Elapsed.track
    def update(self, source, target, node, item):
        # Determine item key
        # TODO this should be moved to a separate method:
        if source == 'anidb':
            key = node.attrib.get('anidbid')

            if target == 'tmdb:movie':
                hash_key = item.identifiers.get('tmdb:movie')

                if hash_key not in node.attrib.get('tmdbid'):
                    raise ValueError('Mismatch detected between "tmdbid" and "tmdbmid", both identifiers should match')
            elif target in item.identifiers:
                hash_key = item.identifiers.get(target)
            else:
                raise ValueError('Unknown target: %r' % (target,))
        elif source == 'tmdb:movie':
            key = item.identifiers.get('tmdb:movie')
            hash_key = item.identifiers.get('anidb')

            if key not in node.attrib.get('tmdbid'):
                raise ValueError('Mismatch detected between "tmdbid" and "tmdbmid", both identifiers should match')
        elif source in item.identifiers:
            key = item.identifiers.get(source)
            hash_key = item.identifiers.get('anidb')
        else:
            raise ValueError('Unknown source: %r' % (source,))

        # Update items
        updated = False

        for service_key in key.split(','):
            if service_key == 'unknown':
                continue

            # Update item identifiers
            item.identifiers[source] = service_key

            # Process item update
            i_success, i_updated = self.update_one(source, service_key, hash_key, item)

            if not i_success:
                return False, i_updated

            updated |= i_updated

        return True, updated

    @Elapsed.track
    def update_one(self, service, service_key, hash_key, item):
        # Construct hash of `item`
        hash = item.hash()

        # Check if item has already been seen
        if (service, service_key) in self.seen:
            # Add item to `previous` object (and convert to "multiple" structure if needed)
            previous = self.seen[(service, service_key)]

            if not previous.add(item, service):
                return False, False

            # Update `current` item
            current = previous
        else:
            # Update `current` item
            current = item

            # Update seen keys
            self.seen[(service, service_key)] = current

        # Try retrieve item metadata from collection
        metadata = self.collection.get(service_key)

        if metadata:
            # Ensure `item` doesn't match metadata (already up to date)
            if (service, service_key) in self.updated:
                log.debug('Updating item: %s/%s', service, service_key)
            elif metadata.hashes.get(hash_key) == hash:
                # Ensure no duplicate hashes exist
                if len(metadata.hashes) == len(set(metadata.hashes.values())):
                    return True, False
            elif hash_key in metadata.hashes:
                log.debug('Updating item: %s/%s (%r != %r)', service, service_key, metadata.hashes[hash_key], hash)
        else:
            # Construct new index item
            metadata = self.collection.index.create(service_key)

            # Update index
            self.collection.set(service_key, metadata)

        # Mark item as updated
        self.updated[(service, service_key)] = True

        # Update item
        # log.debug('[%-5s] Updating item: %r (revision: %r)', service, service_key, metadata.revision)

        if not metadata.update(current, hash_key, hash):
            log.warn('[%-5s] Unable to update item: %r', service, service_key)

        return True, True
