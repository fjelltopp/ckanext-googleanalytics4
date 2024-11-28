from sqlalchemy import MetaData
from sqlalchemy.sql import select, text
from sqlalchemy import func

import ckan.model as model
from ckan.lib.base import *


cached_tables = {}


def _get_table(name):
    if name not in cached_tables:
        meta = MetaData()
        meta.reflect(bind=model.meta.engine)
        table = meta.tables[name]
        cached_tables[name] = table
    return cached_tables[name]


def _update_visits(table_name, item_id, recently, ever):
    stats = _get_table(table_name)
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
    
    model.Session.commit()


def _get_visits(table_name, item_id):
    connection = model.Session.connection()
    stats = _get_table(table_name)
    id_col_name = "%s_id" % table_name[: -len("_stats")]
    id_col = getattr(stats.c, id_col_name)
    s = select(
        [stats.c.visits_ever]
    ).where(id_col == item_id)
    res = connection.execute(s).fetchone()
    return res and res or [0]
