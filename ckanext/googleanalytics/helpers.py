from .utils.numerize import numerize
from ckan.plugins import toolkit


def get_package_stats(package_id):
    package_stat = toolkit.get_action('package_stats')({}, {'package_id': package_id})
    return numerize(int(package_stat))


def get_resource_stats(resource_id):
    resource_stat = toolkit.get_action('resource_stats')({}, {'resource_id': resource_id})
    return numerize(int(resource_stat))


def get_url_stats(url_id):
    url_stat = toolkit.get_action('url_stats')({}, {'url_id': url_id})
    return numerize(int(url_stat))
