from . import dbutil
from ckan.plugins import toolkit
import json
import logging
from .cli import init_ga4_service, get_ga4_data2, save_ga_data


log = logging.getLogger(__name__)

@toolkit.side_effect_free
def resource_stat(context, data_dict):
    '''
    Fetch resource stats
    '''
    resource_id = data_dict['resource_id']
    result = dbutil.get_resource_stat(resource_id)[0]
    return json.dumps(result)

@toolkit.side_effect_free
def package_stat(context, data_dict):
    '''
    Fetch package stats
    '''
    package_id = data_dict['package_id']
    try:
        result = dbutil.get_package_stat(package_id)[0]
    except Exception as e:
        log.error("Package not in package_stat: {}".format(e))
    return json.dumps(result)


def download_package_stat(context, data_dict):
    '''
    Download package stats from Google analytics into the local database
    '''
    credentials_path = data_dict['credentials_path']
    service = init_ga4_service(credentials_path)
    packages_data = get_ga4_data2(service)
    save_ga_data(packages_data)
    return json.dumps({
        'package_count': len(packages_data)
    })
