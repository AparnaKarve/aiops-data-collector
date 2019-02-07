"""Target Worker library.

With the help of this library a target worker can be assigned on-the-fly
The library also provides all necessary information to the worker to process
the GET requests
"""

import logging
import os
import sys

logger = logging.getLogger()

if os.environ.get('INPUT_DATA_FORMAT') == 'TOPOLOGY':
    logger.info('Target Worker is Topology')

    USERNAME = os.environ.get('USERNAME')
    PASSWORD = os.environ.get('PASSWORD')
    ENDPOINT = os.environ.get('TOPOLOGY_INVENTORY_ENDPOINT')

    if not all((USERNAME, PASSWORD, ENDPOINT)):
        logger.error('Environment not set properly, '
                     'missing USERNAME or PASSWORD or '
                     'TOPOLOGY_INVENTORY_ENDPOINT')
        sys.exit(1)

    NAME = 'worker_topology'
    INFO = {
        'endpoint': ENDPOINT,
        'auth': (USERNAME, PASSWORD),
        'queries': {
            'container_nodes': 'archived_at',
            'volume_attachments': '',
            'volumes': 'archived_at',
            'volume_types': 'archived_at'
        }
    }


else:
    logger.info('Target Worker is Clustering')

    NAME = 'worker_clustering'
    INFO = {}


__all__ = ['NAME', 'INFO']
