from prometheus_client import Counter

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
    'data_download_inprogress_requests',
    'The total number of data download inprogress requests'
)
data_download_request_exceptions = Counter(   #noqa
    'data_download_inprogress_request_exceptions',
    'The total number of data download inprogress request exceptions'
)
post_data_requests_total = Counter(   #noqa
    'post_data_inprogress_requests',
    'The total number of post data inprogress requests'
)
post_data_request_exceptions = Counter(   #noqa
    'post_data_inprogress_request_exceptions',
    'The total number of post data inprogress request exceptions'
)
