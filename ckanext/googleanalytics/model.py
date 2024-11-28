from sqlalchemy import Table, Column, Integer, String, MetaData

import ckan.model as model
from ckan.lib.base import *

from ckanext.googleanalytics.utils.db import _update_visits, _get_visits


def init_tables():
    metadata = MetaData()
    package_stats = Table(
        "package_stats",
        metadata,
        Column("package_id", String(60), primary_key=True),
        Column("visits_recently", Integer),
        Column("visits_ever", Integer),
    )
    resource_stats = Table(
        "resource_stats",
        metadata,
        Column("resource_id", String(60), primary_key=True),
        Column("visits_recently", Integer),
        Column("visits_ever", Integer),
    )
    url_stats = Table(
        "url_stats",
        metadata,
        Column("url_id", String(512), primary_key=True),
        Column("visits_recently", Integer),
        Column("visits_ever", Integer),
    )
    metadata.create_all(model.meta.engine)


def update_package_visits(package_id, recently, ever):
    return _update_visits("package_stats", package_id, recently, ever)


def update_resource_visits(resource_id, recently, ever):
    return _update_visits("resource_stats", resource_id, recently, ever)


def update_url_visits(url_id, recently, ever):
    return _update_visits("url_stats", url_id, recently, ever)

 
def get_package_stat(package_id):
    return _get_visits("package_stats", package_id)


def get_resource_stat(resource_id):
    return _get_visits("resource_stats", resource_id)


def get_url_stat(url_id):
    return _get_visits("url_stats", url_id)
