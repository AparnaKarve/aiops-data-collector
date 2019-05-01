import base64
import json
import logging
import math

import pandas as pd

from threading import current_thread

import prometheus_metrics
from . import utils
from .env import HOST_INVENTORY_HOST, HOST_INVENTORY_PATH

LOGGER = logging.getLogger()
URL = f'{HOST_INVENTORY_HOST}/{HOST_INVENTORY_PATH}'


def _retrieve_hosts(headers: dict) -> dict:
    """Collect all hosts for account.

    Parameters
    ----------
    headers (dict)
        HTTP Headers that will be used to request data

    Returns
    -------
    dict
        Host collection

    """
    url = URL + '/hosts?page={}'
    url_profile = URL + '/hosts/{}/system_profile'

    # Perform initial request
    prometheus_metrics.METRICS['gets'].inc()
    resp = utils.retryable('get', url.format(1), headers=headers)
    prometheus_metrics.METRICS['get_successes'].inc()
    resp = resp.json()
    total = resp['total']
    # Iterate next pages if any
    pages = math.ceil(total / resp['per_page'])

    ids = ','.join([x['id'] for x in resp['results']])
    prometheus_metrics.METRICS['gets'].inc()
    resp = utils.retryable('get', url_profile.format(ids), headers=headers)
    prometheus_metrics.METRICS['get_successes'].inc()
    results = resp.json()['results']
    for page in range(2, pages+1):
        prometheus_metrics.METRICS['gets'].inc()
        resp = utils.retryable('get', url.format(page), headers=headers)
        prometheus_metrics.METRICS['get_successes'].inc()
        ids = ','.join([x['id'] for x in resp.json()['results']])
        prometheus_metrics.METRICS['gets'].inc()
        resp = utils.retryable('get', url_profile.format(ids), headers=headers)
        prometheus_metrics.METRICS['get_successes'].inc()
        results += resp.json()['results']

    epd = pd.DataFrame(results)
    # epd.to_csv(f'/Users/akarve/rh/aiops/aiops-dummy-ai-service/outlier_detection_csvs/{account_id}_hostinv.csv')
    epd.to_csv(f'/opt/app-root/src/0501_hostinv.csv')

    return dict(results=results, total=total)


def worker(_: str, source_id: str, dest: str, b64_identity: str) -> None:
    """Worker for host inventory.

    Parameters
    ----------
    _ (str)
        Skipped
    source_id (str)
        Job identifier
    dest (str)
        URL where to pass data
    b64_identity (str)
        Red Hat Identity base64 string

    """
    thread = current_thread()
    LOGGER.debug('%s: Worker started', thread.name)

    identity = json.loads(base64.b64decode(b64_identity))
    account_id = identity.get('identity', {}).get('account_number')
    LOGGER.debug('to retrieve hosts of account_id: %s', account_id)

    # TO-DO: Check cached account list before proceed

    headers = {"x-rh-identity": b64_identity}

    try:
        out = _retrieve_hosts(headers)
    except utils.RetryFailedError as exception:
        prometheus_metrics.METRICS['get_errors'].inc()
        LOGGER.error(
            '%s: Unable to fetch source data for "%s": %s',
            thread.name, source_id, exception
        )
        return
    LOGGER.debug(
        'Received data for account_id=%s has total=%s',
        account_id, out.get('total')
    )

    # Build the POST data object
    data = {
        'account': account_id,
        'data': out,
    }

    # Pass to next service
    prometheus_metrics.METRICS['posts'].inc()
    try:
        utils.retryable('post', dest, json=data, headers=headers)
        prometheus_metrics.METRICS['post_successes'].inc()
    except utils.RetryFailedError as exception:
        LOGGER.error(
            '%s: Failed to pass data for "%s": %s',
            thread.name, source_id, exception
        )
        prometheus_metrics.METRICS['post_errors'].inc()

    LOGGER.debug('%s: Done, exiting', thread.name)
