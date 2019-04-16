import logging
import os
from threading import current_thread

import base64
import json
import yaml

import prometheus_metrics
from . import utils
from .env import (APP_NAME, TENANTS_URL, ALL_TENANTS,
                  TOPOLOGICAL_INVENTORY_HOST, TOPOLOGICAL_INVENTORY_PATH)

LOGGER = logging.getLogger()
CFG_DIR = '{}/configs'.format(os.path.dirname(__file__))
BASE_URL = f'{TOPOLOGICAL_INVENTORY_HOST}/{TOPOLOGICAL_INVENTORY_PATH}'


def _load_yaml(filename: str) -> dict:
    """Yaml filename loader helper.

    Parameters
    ----------
    filename (str)
        Yaml file to load

    Returns
    -------
    dict
        YAML content as Pythonic dict

    """
    with open(filename) as yaml_file:
        return yaml.full_load(yaml_file)


APP_CONFIG = _load_yaml(f'{CFG_DIR}/topological_app_config.yml').get(APP_NAME)
QUERIES = _load_yaml(f'{CFG_DIR}/topological_queries.yml')


def _update_fk(page_data: list, fk_name: str, fk_id: str) -> dict:
    """Mutate Rows with Foreign key info.

    Updates foreign key values for each entry in given page_data

    Parameters
    ----------
    page_data (list)
        Data on a page which should be modified
    fk_name (str)
        Column where the Foreign Key is located
    fk_id (str)
        Foreign Key value

    Returns
    -------
    list
        Updated page_data

    """
    if not (fk_name and fk_id):
        return page_data

    for row in page_data:
        row[fk_name] = fk_id
    return page_data


def _collect_data(url: str, fk_name: str = None,
                  fk_id: str = None, headers: dict = None) -> dict:
    """Aggregate data from all pages.

    Returns data aggregated from all pages together

    Parameters
    ----------
    url (str)
        URI to the first page, where to start the traverse
    fk_name (str)
        Foreign key column to update if needed
    fk_id (str)
        Foreign key value to update if needed

    Returns
    -------
    dict
        All data aggregated across all pages

    Raises
    ------
    utils.RetryFailedError
        Connection failed, data is not complete

    """
    # Collect data from the first page
    prometheus_metrics.METRICS['gets'].inc()
    resp = utils.retryable('get', url, headers=headers)
    prometheus_metrics.METRICS['get_successes'].inc()
    resp = resp.json()
    all_data = resp['data']

    # Walk all pages
    while resp['links'].get('next'):
        prometheus_metrics.METRICS['gets'].inc()
        resp = utils.retryable(
            'get',
            f'{TOPOLOGICAL_INVENTORY_HOST}{resp["links"]["next"]}',
            headers=headers
        )
        resp = resp.json()
        prometheus_metrics.METRICS['get_successes'].inc()
        all_data += resp['data']

    return _update_fk(all_data, fk_name, fk_id)


def _query_main_collection(collection: str, headers: dict = None) -> dict:
    """Query a Collection.

    Parameters
    ----------
    collection (str)
        A collection to download

    Returns
    -------
    dict
        All data aggregated across all pages

    Raises
    ------
    utils.RetryFailedError
        Connection failed, data is not complete

    """
    return _collect_data(f'{BASE_URL}/{collection}', headers=headers)


def _query_sub_collection(
        main_collection: str,
        sub_collection: str,
        data: dict,
        foreign_key: str,
        headers: dict = None
) -> dict:
    """Query a SubCollection for all records in the main collection.

    Parameters
    ----------
    main_collection (str)
        A parent collection pointer
    sub_collection (str)
        A collection to download
    data (dict)
        Already available data for reference
    foreign_key (str)
        Foreign key column to be populated in sub-collection records

    Returns
    -------
    dict
        All data aggregated across all pages

    Raises
    ------
    utils.RetryFailedError
        Connection failed, data is not complete

    """
    url = f'{BASE_URL}/{main_collection}/{{}}/{sub_collection}'
    all_data = []
    for item in data[main_collection]:
        all_data += _collect_data(url.format(item['id']), foreign_key,
                                  item['id'], headers=headers)
    return all_data


def worker(_: str, source_id: str, dest: str, b64_identity: str) -> None:
    """Worker for topological inventory.

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

    headers = {"x-rh-identity": b64_identity}

    if ALL_TENANTS:
        resp = utils.retryable('get', TENANTS_URL, headers=headers)
        tenants_headers = \
            [tenant_header_info(t["external_tenant"]) for t in resp.json()]

        LOGGER.info('Fetching data for ALL(%s) Tenants', len(tenants_headers))

        for tenant_header in tenants_headers:
            LOGGER.debug('%s: ---START Account# %s---',
                         thread.name, tenant_header['acct_no'])
            headers = tenant_header['headers']
            topological_inventory_data(_, source_id, dest, headers, thread)
            LOGGER.debug('%s: ---END Account# %s---',
                         thread.name, tenant_header['acct_no'])
    else:
        LOGGER.info('Fetching data for current Tenant')
        topological_inventory_data(_, source_id, dest, headers, thread)

    LOGGER.debug('%s: Done, exiting', thread.name)


def topological_inventory_data(
        _: str,
        source_id: str,
        dest: str,
        headers: dict,
        thread
) -> None:
    """Generate Tenant data for topological inventory.

    Parameters
    ----------
    _ (str)
        Skipped
    source_id (str)
        Job identifier
    dest (str)
        URL where to pass data
    headers (dict)
        RH Identity header
    thread
        Current Thread

    """
    # Build the POST data object
    data = {
        'id': source_id,
        'data': {}
    }

    for entity in APP_CONFIG:
        query_spec = QUERIES[entity]
        main_collection = query_spec.get('main_collection')
        sub_collection = query_spec.get('sub_collection')
        foreign_key = query_spec.get('foreign_key')

        if sub_collection:
            try:
                all_data = _query_sub_collection(
                    main_collection,
                    sub_collection,
                    data['data'],
                    foreign_key,
                    headers=headers
                )
            except utils.RetryFailedError as exception:
                prometheus_metrics.METRICS['get_errors'].inc()
                LOGGER.error(
                    '%s: Unable to fetch source data for "%s": %s',
                    thread.name, source_id, exception
                )
                return
        else:
            try:
                all_data = _query_main_collection(
                    main_collection,
                    headers=headers
                )
            except utils.RetryFailedError as exception:
                prometheus_metrics.METRICS['get_errors'].inc()
                LOGGER.error(
                    '%s: Unable to fetch source data for "%s": %s',
                    thread.name, source_id, exception
                )
                return

        LOGGER.info(
            '%s: %s: %s\t%s',
            thread.name, source_id, entity, len(all_data)
        )

        if all_data:
            data['data'][entity] = all_data
        else:
            LOGGER.debug(
                '%s: Inadequate Topological Inventory data for this account.',
                thread.name
            )
            return

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


def tenant_header_info(acct_no):
    """Return a dict containing Account No. and it's b64 Identity header."""
    rh_identity = dict(identity=dict(account_number=acct_no))
    b64_identity = base64.b64encode(json.dumps(rh_identity).encode())
    return {'acct_no': acct_no, 'headers': {'x-rh-identity': b64_identity}}
