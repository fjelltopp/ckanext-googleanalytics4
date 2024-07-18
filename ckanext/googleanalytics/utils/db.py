import logging

from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.sql import select, text
from sqlalchemy import func

import ckan.model as model
from ckan.lib.base import *

from . import (
    RESOURCE_URL_REGEX, PACKAGE_URL,
    _resource_url_tag,
    _recent_view_days
)


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


def update_resource_visits(resource_id, recently, ever):
    return _update_visits("resource_stats", resource_id, recently, ever)


def update_package_visits(package_id, recently, ever):
    return _update_visits("package_stats", package_id, recently, ever)


def get_resource_visits_for_url(url):
    connection = model.Session.connection()
    count = connection.execute(
        text(
            """SELECT visits_ever FROM resource_stats, resource
        WHERE resource_id = resource.id
        AND resource.url = :url"""
        ),
        url=url,
    ).fetchone()
    return count and count[0] or ""


def get_top_packages(limit=20):
    """ get_top_packages is broken, and needs to be rewritten to work with
    CKAN 2.*. This is because ckan.authz has been removed in CKAN 2.*

    See commit ffa86c010d5d25fa1881c6b915e48f3b44657612
    """
    items = []
    # caveat emptor: the query below will not filter out private
    # or deleted datasets (TODO)
    q = model.Session.query(model.Package)
    connection = model.Session.connection()
    package_stats = get_table("package_stats")
    s = select(
        [
            package_stats.c.package_id,
            package_stats.c.visits_recently,
            package_stats.c.visits_ever,
        ]
    ).order_by(package_stats.c.visits_ever.desc())
    res = connection.execute(s).fetchmany(limit)
    for package_id, recent, ever in res:
        item = q.filter(text("package.id = '%s'" % package_id))
        if not item.count():
            continue
        items.append((item.first(), recent, ever))
    return items


def get_top_resources(limit=20):
    items = []
    connection = model.Session.connection()
    resource_stats = get_table("resource_stats")
    s = select(
        [
            resource_stats.c.resource_id,
            resource_stats.c.visits_recently,
            resource_stats.c.visits_ever,
        ]
    ).order_by(resource_stats.c.visits_recently.desc())
    res = connection.execute(s).fetchmany(limit)
    for resource_id, recent, ever in res:
        item = model.Session.query(model.Resource).filter(
            "resource.id = '%s'" % resource_id
        )
        if not item.count():
            continue
        items.append((item.first(), recent, ever))
    return items


def get_resource_stat(resource_id):
    connection = model.Session.connection()
    resource_stats = get_table("resource_stats")
    s = select(
        [resource_stats.c.visits_ever]
    ).where(resource_stats.c.resource_id == resource_id)
    res = connection.execute(s).fetchone()
    return res and res or [0]

def get_package_stat(package_id):
    connection = model.Session.connection()
    package_stats = get_table("package_stats")
    s = select(
        [package_stats.c.visits_ever]
    ).where(package_stats.c.package_id == package_id)
    res = connection.execute(s).fetchone()
    return res and res or [0]


def save_packages(packages_data, summary_date):
    engine = model.meta.engine
    # clear out existing data before adding new
    sql = (
        """DELETE FROM tracking_summary
             WHERE tracking_date='%s'; """
        % summary_date
    )
    engine.execute(sql)

    for url, count in list(packages_data.items()):
        # If it matches the resource then we should mark it as a resource.
        # For resources we don't currently find the package ID.
        if RESOURCE_URL_REGEX.match(url):
            tracking_type = "resource"
        else:
            tracking_type = "page"

        sql = """INSERT INTO tracking_summary
                 (url, count, tracking_date, tracking_type)
                 VALUES (%s, %s, %s, %s);"""
        engine.execute(sql, url, count, summary_date, tracking_type)

    # get ids for dataset urls
    sql = """UPDATE tracking_summary t
             SET package_id = COALESCE(
                 (SELECT id FROM package p WHERE t.url =  %s || p.name)
                 ,'~~not~found~~')
             WHERE t.package_id IS NULL AND tracking_type = 'page';"""
    engine.execute(sql, PACKAGE_URL)

    # get ids for dataset edit urls which aren't captured otherwise
    sql = """UPDATE tracking_summary t
             SET package_id = COALESCE(
                 (SELECT id FROM package p WHERE t.url =  %s || p.name)
                 ,'~~not~found~~')
             WHERE t.package_id = '~~not~found~~' AND tracking_type = 'page';"""
    engine.execute(sql, "%sedit/" % PACKAGE_URL)

    # update summary totals for resources
    sql = """UPDATE tracking_summary t1
             SET running_total = (
                SELECT sum(count)
                FROM tracking_summary t2
                WHERE t1.url = t2.url
                AND t2.tracking_date <= t1.tracking_date
             ) + t1.count
             ,recent_views = (
                SELECT sum(count)
                FROM tracking_summary t2
                WHERE t1.url = t2.url
                AND t2.tracking_date <= t1.tracking_date AND t2.tracking_date >= t1.tracking_date - %s
             ) + t1.count
             WHERE t1.running_total = 0 AND tracking_type = 'resource';"""
    engine.execute(sql, _recent_view_days())

    # update summary totals for pages
    sql = """UPDATE tracking_summary t1
             SET running_total = (
                SELECT sum(count)
                FROM tracking_summary t2
                WHERE t1.package_id = t2.package_id
                AND t2.tracking_date <= t1.tracking_date
             ) + t1.count
             ,recent_views = (
                SELECT sum(count)
                FROM tracking_summary t2
                WHERE t1.package_id = t2.package_id
                AND t2.tracking_date <= t1.tracking_date AND t2.tracking_date >= t1.tracking_date - %s
             ) + t1.count
             WHERE t1.running_total = 0 AND tracking_type = 'page'
             AND t1.package_id IS NOT NULL
             AND t1.package_id != '~~not~found~~';"""
    engine.execute(sql, _recent_view_days())
