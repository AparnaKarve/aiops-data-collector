import os

TENANTS_URL = os.environ.get('TENANTS_URL')
ALL_TENANTS = os.environ.get('ALL_TENANTS', 'true').lower() in ['true', 'y']
TOPOLOGICAL_INVENTORY_HOST = os.environ.get('TOPOLOGICAL_INVENTORY_HOST')
TOPOLOGICAL_INVENTORY_PATH = os.environ.get('TOPOLOGICAL_INVENTORY_PATH')
HOST_INVENTORY_HOST = os.environ.get('HOST_INVENTORY_HOST')
HOST_INVENTORY_PATH = os.environ.get('HOST_INVENTORY_PATH')
INPUT_DATA_FORMAT = os.environ.get('INPUT_DATA_FORMAT', '').upper()
APP_NAME = os.environ.get('APP_NAME')
SSL_VERIFY = os.environ.get('SSL_VERIFY', 'true').lower() in ['true', 'y']
