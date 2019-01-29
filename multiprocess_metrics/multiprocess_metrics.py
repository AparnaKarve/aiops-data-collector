import os

# all gunicorn processes in a given instance need to access a common
# folder in /tmp where the metrics can be recorded
PROMETHEUS_MULTIPROC_DIR = '/tmp/aiops_data_collector'


def multiprocess_metrics_prereq():
    """Multiprocess Metrics Prerequisite ."""
    os.makedirs(PROMETHEUS_MULTIPROC_DIR, exist_ok=True)
    os.environ['prometheus_multiproc_dir'] = PROMETHEUS_MULTIPROC_DIR
