import hashlib
import json
import logging
import requests
import threading

import ckan.plugins.toolkit as toolkit
import ckan.model as model

from ckanext.googleanalytics.utils.ga import (
    _init_service,
    _get_packages_data,
    _save_packages_data,
    _get_urls_data,
    _save_urls_data
)


log = logging.getLogger(__name__)


class AnalyticsPostThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            data = self.queue.get()
            log.debug("Sending API event to Google Analytics: GA4")
            measurement_id = toolkit.config.get("googleanalytics.measurement_id")
            api_secret = toolkit.config.get("googleanalytics.api_secret")
            res = requests.post(
                "https://www.google-analytics.com/mp/collect?measurement_id={}&api_secret={}".format(measurement_id, api_secret),
                data=json.dumps(data),
                timeout=10,
            )
            self.queue.task_done()


def post_analytics(user):
    from ckanext.googleanalytics.plugin import GoogleAnalyticsPlugin
    
    path = toolkit.request.environ["PATH_INFO"]
    path_id = path.split("/dataset/")[1].split("/")[0]
    context = {
        u"model": model,
        u"session": model.Session,
        u"user": user
    }
    package = toolkit.get_action("package_show")(context, {"id": path_id})
    referer_link = "/dataset/{}".format(package.get("name"))

    resource_data = {
        "client_id": hashlib.md5(six.ensure_binary(toolkit.c.user)).hexdigest(),
        "events": [
            {
                "name": "file_download",
                "params" : {
                    "link_url": referer_link
                }
            }
        ]
    }

    GoogleAnalyticsPlugin.analytics_queue.put(resource_data)


def load_package_stats(credentials):
    service = _init_service(credentials)
    packages_data = _get_packages_data(service)
    _save_packages_data(packages_data)
    return packages_data


def load_url_stats(credentials):
    service = _init_service(credentials)
    urls_data = _get_urls_data(service)
    _save_urls_data(urls_data)
    return urls_data
