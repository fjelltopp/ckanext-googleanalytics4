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


def save_ga_data(packages_data):
    """Save tuples of packages_data to the database"""
    def save_resource(resource_id, visits):
        dbutil.update_resource_visits(resource_id, visits["recent"], visits["ever"])
        log.info("Updated resource %s with %s visits" % (resource.id, visits))

    def save_package(package_id, visits):
        dbutil.update_package_visits(package_id, visits["recent"], visits["ever"])
        log.info("Updated package %s with %s visits" % (package_id, visits))
    
    packages = {}
    for identifier, visits in packages_data.items():
        matches = RESOURCE_URL_REGEX.match(identifier)
        
        if matches:
            resource_url = identifier.replace(matches.group(1), "")
            package_id = matches.group(2)
            resource_id = matches.group(3)
            
            connection = model.Session.connection()
            resource = (
                model.Session.query(model.Resource)
                .autoflush(True)
                .filter(model.Resource.id.like(resource_id + "%"))
                .first()
            )
            if not resource:
                log.warning("Couldn't find resource %s" % resource_url)
                continue

            # we have a valid resource, we save it
            save_resource(resource.id, visits)
            
            # each resource is associated with a dataset/package it belongs to
            # therefore to update a package, we watch their corresponding resources
            if package_id in packages:
                packages[package_id]["recent"] += visits["recent"]
                packages[package_id]["ever"] += visits["ever"]
            else:
                packages[package_id] = {
                    "recent": visits["recent"],
                    "ever": visits["ever"]
                }
        
        # update packages
        for package_id, visits in packages.items():
            save_package(package_id, visits)
    
    model.Session.commit()
