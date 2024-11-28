import logging

from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.sql import select, text
from sqlalchemy import func

import ckan.model as model
from ckan.lib.base import *


log = logging.getLogger(__name__)
cached_tables = {}


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


def get_table(name):
    if name not in cached_tables:
        meta = MetaData()
        meta.reflect(bind=model.meta.engine)
        table = meta.tables[name]
        cached_tables[name] = table
    return cached_tables[name]


def _update_visits(table_name, item_id, recently, ever):
    stats = get_table(table_name)
    id_col_name = "%s_id" % table_name[: -len("_stats")]
    id_col = getattr(stats.c, id_col_name)
    s = select([func.count(id_col)], id_col == item_id)
    connection = model.Session.connection()
    count = connection.execute(s).fetchone()
    if count and count[0]:
        connection.execute(
            stats.update()
            .where(id_col == item_id)
            .values(visits_recently=recently, visits_ever=ever)
        )
    else:
        values = {
            id_col_name: item_id,
            "visits_recently": recently,
            "visits_ever": ever,
        }
        connection.execute(stats.insert().values(**values))


def update_package_visits(package_id, recently, ever):
    return _update_visits("package_stats", package_id, recently, ever)


def update_resource_visits(resource_id, recently, ever):
    return _update_visits("resource_stats", resource_id, recently, ever)


def update_url_visits(url_id, recently, ever):
    return _update_visits("url_stats", url_id, recently, ever)


def _get_stats(table_name, item_id):
    connection = model.Session.connection()
    stats = get_table(table_name)
    id_col_name = "%s_id" % table_name[: -len("_stats")]
    id_col = getattr(stats.c, id_col_name)
    s = select(
        [stats.c.visits_ever]
    ).where(id_col == item_id)
    res = connection.execute(s).fetchone()
    return res and res or [0]

 
def get_package_stat(package_id):
    return _get_stats("package_stats", package_id)


def get_resource_stat(resource_id):
    return _get_stats("resource_stats", resource_id)


def get_url_stat(url_id):
    return _get_stats("url_stats", url_id)
