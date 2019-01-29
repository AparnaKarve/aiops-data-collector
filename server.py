import logging
import os
import sys

from flask import Flask, jsonify, request
from flask.logging import default_handler
from gunicorn.arbiter import Arbiter

import workers

from collect_json_schema import CollectJSONSchema

import multiprocess_metrics


ROOT_LOGGER = logging.getLogger()
ROOT_LOGGER.addHandler(default_handler)

import prometheus_metrics

# try:
#     multiprocess_metrics.multiprocess_metrics_prereq()
#     import prometheus_metrics
# except IOError as e:
#     # this is a non-starter for scraping metrics in the
#     # Multiprocess Mode (Gunicorn)
#     # terminate if there is an exception here
#     ROOT_LOGGER.error(
#         "Error while creating prometheus_multiproc_dir: %s", e
#     )
#     sys.exit(Arbiter.APP_LOAD_ERROR)


def create_application():
    """Create Flask application instance with AWS client enabled."""
    app = Flask(__name__)
    app.config['NEXT_MICROSERVICE_HOST'] = \
        os.environ.get('NEXT_MICROSERVICE_HOST')

    return app


APP = create_application()

ROOT_LOGGER.setLevel(APP.logger.level)

VERSION = "0.0.1"

# Schema for the Collect API
SCHEMA = CollectJSONSchema()


@APP.route("/api/v0/version", methods=['GET'])
def get_version():
    """Endpoint for getting the current version."""
    return jsonify(
        status='OK',
        version=VERSION,
        message='AIOPS Data Collector Version 0.0.1'
    )


@APP.route("/api/v0/collect", methods=['POST'])
def post_collect():
    """Endpoint servicing data collection."""
    input_data = request.get_json(force=True)
    validation = SCHEMA.load(input_data)

    prometheus_metrics.METRICS['jobs_total'].inc()

    if validation.errors:
        prometheus_metrics.METRICS['jobs_denied'].inc()
        return jsonify(
            status='Error',
            errors=validation.errors,
            message='Input payload validation failed'
        ), 400

    next_service = APP.config['NEXT_MICROSERVICE_HOST']
    source_id = input_data.get('payload_id')

    workers.download_job(input_data['url'], source_id, next_service)
    APP.logger.info('Job started.')

    prometheus_metrics.METRICS['jobs_initiated'].inc()
    return jsonify(status="OK", message="Job initiated")


@APP.route("/metrics", methods=['GET'])
def metrics():
    """Metrics Endpoint."""
    return prometheus_metrics.generate_aggregated_metrics()


if __name__ == "__main__":
    # pylama:ignore=C0103
    port = int(os.environ.get("PORT", 8004))
    APP.run(port=port)
