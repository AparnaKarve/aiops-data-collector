import logging
from threading import current_thread

import requests

from .env import SSL_VERIFY

CHUNK = 10240
MAX_RETRIES = 3
LOGGER = logging.getLogger()

# pylama:ignore=E1101
requests.packages.urllib3.disable_warnings()


class RetryFailedError(requests.HTTPError):
    """Exception raised when the HTTP retry fails.

    Behaves as requests.HTTPError.
    """


def retryable(method: str, *args, **kwargs) -> requests.Response:
    """Retryable HTTP request.

    Invoke a "method" on "requests.session" with retry logic.
    :param method: "get", "post" etc.
    :param *args: Args for requests (first should be an URL, etc.)
    :param **kwargs: Kwargs for requests
    :return: Response object
    :raises: HTTPError when all requests fail
    """
    thread = current_thread()
    request_kwargs = dict(verify=False)
    request_kwargs.update(kwargs)

    with requests.Session() as session:
        for attempt in range(MAX_RETRIES):
            try:
                resp = getattr(session, method)(*args, **request_kwargs)

                resp.raise_for_status()
            except (requests.HTTPError, requests.ConnectionError) as e:
                LOGGER.warning(
                    '%s: Request failed (attempt #%d), retrying: %s',
                    thread.name, attempt, str(e)
                )
                continue
            else:
                return resp

    raise RetryFailedError('All attempts failed')
