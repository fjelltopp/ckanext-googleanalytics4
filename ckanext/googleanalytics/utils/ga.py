import httplib2
import logging

from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build

from ckan.exceptions import CkanVersionException
import ckan.plugins.toolkit as tk

from . import (
    RESOURCE_URL_REGEX, PACKAGE_URL,
    _resource_url_tag,
    _recent_view_days
)


config = tk.config
log = logging.getLogger(__name__)


def init_service(credentials_path):
    scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scopes)
    http = httplib2.Http()
    http = credentials.authorize(http)
   
    service = build('analyticsdata', 'v1beta', http=http, cache_discovery=False)
    return service


def get_packages_data(service):
    packages = {}
    property_id = tk.config.get("googleanalytics.property_id")
    dates = {
        "recent": {"startDate": "{}daysAgo".format(_recent_view_days()), "endDate": "today"},
        "ever": {"startDate": "2024-01-01", "endDate": "today"}
    }

    for date_name, date in dates.items():
        request_body = {
            "requests": [{
                "dateRanges": [date],
                "metrics": [{"name": "eventCount"}],
                "dimensions": [{"name": "eventName"}, {"name": "linkUrl"}]
            }]
        }
        
        response = service.properties().batchRunReports(
            body=request_body, property='properties/{}'.format(property_id)
        ).execute()
        
        for report in response.get('reports', []):
            for row in report.get('rows', []):
                event_category = row['dimensionValues'][0].get('value', '')
                event_label = row['dimensionValues'][1].get('value', '')
                event_count = row['metricValues'][0].get('value', 0)

                if event_category == "file_download":
                    package = event_label
                    count = event_count
                    if "/" in package:
                        if not package.startswith(PACKAGE_URL):
                            package = "/" + "/".join(package.split("/")[2:])
                        
                        val = 0
                        if package in packages and date_name in packages[package]:
                            val += packages[package][date_name]
                        packages.setdefault(package, {})[date_name] = int(count) + val
    return packages


def save_packages_data(packages_data):
    """Save tuples of packages_data to the database"""
    for identifier, visits in list(packages_data.items()):
        recently = visits.get("recent", 0)
        ever = visits.get("ever", 0)
        matches = RESOURCE_URL_REGEX.match(identifier)
        if matches:
            resource_url = identifier[len(_resource_url_tag()) :]
            resource = (
                model.Session.query(model.Resource)
                .autoflush(True)
                .filter_by(id=matches.group(1))
                .first()
            )
            if not resource:
                log.warning("Couldn't find resource %s" % resource_url)
                continue
            db_utils.update_resource_visits(resource.id, recently, ever)
            log.info("Updated %s with %s visits" % (resource.id, visits))
        else:
            f = identifier.split("/dataset/")
            if len(f)>1 :
                g = f[1].split("/")[0]
                package_name = g
            else:
               package_name = identifier[len(PACKAGE_URL) :]
            if "/" in package_name:
                log.warning("%s not a valid package name" % package_name)
                continue
            item = model.Package.get(package_name)
            if not item:
                log.warning("Couldn't find package %s" % package_name)
                continue
            db_utils.update_package_visits(item.id, recently, ever)
            log.info("Updated %s with %s visits" % (item.id, visits))
    model.Session.commit()
