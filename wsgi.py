import logging
# from server import APP
import sys
from gunicorn.arbiter import Arbiter

import multiprocess_metrics

# Sync logging between Flask and Gunicorn
gunicorn_logger = logging.getLogger('gunicorn.error')
# APP.logger.handlers = gunicorn_logger.handlers
# APP.logger.setLevel(gunicorn_logger.level)

print("### Hello ####")

try:
    multiprocess_metrics.multiprocess_metrics_prereq()
    from server import APP

    APP.logger.handlers = gunicorn_logger.handlers
    APP.logger.setLevel(gunicorn_logger.level)
except IOError as e:
    # this is a non-starter for scraping metrics in the
    # Multiprocess Mode (Gunicorn)
    # terminate if there is an exception here
    gunicorn_logger.error(
        "Error while creating prometheus_multiproc_dir: %s", e
    )
    sys.exit(Arbiter.APP_LOAD_ERROR)

# Export "application" variable to gunicorn
# pylama:ignore=C0103
application = APP
