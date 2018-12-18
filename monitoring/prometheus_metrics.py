from prometheus_client import Counter, generate_latest   #noqa

# Prometheus Metrics
data_collector_jobs_total = Counter(   #noqa
    'data_collector_jobs_total',
    'The total number of data collector jobs'
)
data_collector_jobs_initiated_successfully = Counter(   #noqa
    'data_collector_jobs_initiated_successfully',
    'The total number of successfully initiated data collector jobs'
)
data_collector_jobs_denied = Counter(   #noqa
    'data_collector_jobs_denied',
    'The total number of denied data collector jobs'
)
data_download_requests_total = Counter(   #noqa
    'data_download_requests_total',
    'The total number of data download requests'
)
data_download_successful_requests_total = Counter(   #noqa
    'data_download_successful_requests_total',
    'The total number of successful data download requests'
)
data_download_request_exceptions = Counter(   #noqa
    'data_download_request_exceptions',
    'The total number of data download request exceptions'
)
post_data_requests_total = Counter(   #noqa
    'post_data_requests_total',
    'The total number of post data requests'
)
post_data_successful_requests_total = Counter(   #noqa
    'post_data_successful_requests_total',
    'The total number of successful post data requests'
)
post_data_request_exceptions = Counter(   #noqa
    'post_data_request_exceptions',
    'The total number of post data request exceptions'
)
