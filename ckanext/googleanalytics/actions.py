import logging
import json

from ckan.plugins import toolkit

from ckanext.googleanalytics.model import (
    get_package_stat,
    get_resource_stat,
    get_url_stat
)
from ckanext.googleanalytics.logic import load_package_stats

log = logging.getLogger(__name__)


@toolkit.side_effect_free
def package_stat(context, data_dict):
    '''
    Fetch package stats
    '''
    package_id = data_dict['package_id']
    result = 0
    try:
        result = get_package_stat(package_id)[0]
    except Exception as e:
        log.error("Package not found: {}".format(e))
    return json.dumps(result)


@toolkit.side_effect_free
def resource_stat(context, data_dict):
    '''
    Fetch resource stats
    '''
    resource_id = data_dict['resource_id']
    result = 0
    try:
        result = get_resource_stat(resource_id)[0]
    except Exception as e:
        log.error("Resource not found: {}".format(e))
    return json.dumps(result)


@toolkit.side_effect_free
def url_stat(context, data_dict):
    '''
    Fetch url stats
    '''
    url_id = data_dict['url_id']
    result = 0
    try:
        result = get_url_stat(url_id)[0]
    except Exception as e:
        log.error("URL not found: {}".format(e))
    return json.dumps(result)


def download_package_stat(context, data_dict):
    '''
    Download package stats from Google analytics into the local database
    '''
    credentials = data_dict['credentials_path']
    packages_data = ckanext.googleanalytics(credentials)
    return json.dumps({
        'package_count': len(packages_data)
    })
