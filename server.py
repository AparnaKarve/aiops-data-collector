import logging
import os

from flask import Flask, jsonify, request
from flask.logging import default_handler


import workers
from monitoring import prometheus_metrics


def create_application():
    """Create Flask application instance with AWS client enabled."""
    app = Flask(__name__)
    app.config['NEXT_MICROSERVICE_HOST'] = \
        os.environ.get('NEXT_MICROSERVICE_HOST')

    return app


APP = create_application()
ROOT_LOGGER = logging.getLogger()
ROOT_LOGGER.setLevel(APP.logger.level)
ROOT_LOGGER.addHandler(default_handler)


@APP.route("/", methods=['POST'])
def index():
    """Endpoint servicing data collection."""
    input_data = request.get_json(force=True)
    next_service = APP.config['NEXT_MICROSERVICE_HOST']
    source_id = input_data.get('payload_id')

    try:
        workers.download_job(input_data['url'], source_id, next_service)
        APP.logger.info('Job started.')
        prometheus_metrics.data_collector_jobs_total.inc()

    except KeyError as exception:
        APP.logger.warning('No url provided, request denied')
        prometheus_metrics.data_collector_jobs_denied.inc()
        return jsonify(status="FAILED", exception=str(exception)), 400

    prometheus_metrics.data_collector_jobs_initiated_successfully.inc()
    return jsonify(status="OK", message="Job initiated")


if __name__ == "__main__":
    APP.run()
