from prometheus_client import (Counter, Gauge, Summary, Histogram, generate_latest,
                               CollectorRegistry, multiprocess)

# Prometheus Metrics
METRICS = {
    'jobs_total': Counter(
        'aiops_data_collector_jobs_total',
        'The total number of data collector jobs'
    ),
    'jobs_initiated': Counter(
        'aiops_data_collector_jobs_initiated',
        'The total number of successfully initiated data collector jobs'
    ),
    'jobs_denied': Counter(
        'aiops_data_collector_jobs_denied',
        'The total number of denied data collector jobs'
    ),
    'gets': Counter(
        'aiops_data_collector_get_requests_total',
        'The total number of data download requests'
    ),
    'get_successes': Counter(
        'aiops_data_collector_get_requests_successful',
        'The total number of successful data download requests'
    ),
    'get_errors': Counter(
        'aiops_data_collector_get_requests_exceptions',
        'The total number of data download request exceptions'
    ),
    'posts': Counter(
        'aiops_data_collector_post_requests_total',
        'The total number of post data requests'
    ),
    'post_successes': Counter(
        'aiops_data_collector_post_requests_successful',
        'The total number of successful post data requests'
    ),
    'post_errors': Counter(
        'aiops_data_collector_post_requests_exceptions',
        'The total number of post data request exceptions'
    ),
    'data_collection_time': Summary(
        'aiops_data_collector_data_collection_time',
        'Time spent for complete data collection',
        # ['account', 'collection_date']
    ),
    'data_size': Histogram(
        'aiops_data_collector_data_size',
        'Size of data in bytes',
        # ['account', 'collection_date']
    ),
    'data_size_above_ceiling': Gauge(
        'aiops_data_collector_data_size_above_ceiling',
        'Size of data in bytes above ceiling',
        ['account', 'collection_date']
    ),
}


def generate_aggregated_metrics():
    """Generate Aggregated Metrics for multiple processes."""
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return generate_latest(registry)
