# encoding: utf-8
import logging
import click

import ckan.plugins.toolkit as tk
import ckan.model as model
from .utils import (
    db as db_utils,
    ga as ga_utils
)


log = logging.getLogger(__name__)


def get_commands():
    return [googleanalytics]


@click.group(short_help=u"GoogleAnalytics commands")
def googleanalytics():
    pass


@googleanalytics.command()
def init():
    """Initialise the local stats database tables"""
    model.Session.remove()
    model.Session.configure(bind=model.meta.engine)
    db_utils.init_tables()
    log.info("Set up statistics tables in main database")


@googleanalytics.command(short_help=u"Load data from Google Analytics API")
@click.argument("credentials", type=click.Path(exists=True))
@click.option("-s", "--start-date", required=False)
def load(credentials, start_date):
    """Parse data from Google Analytics API and store it
    in a local database
    """
    service = ga_utils.init_service(credentials)
    packages_data = ga_utils.get_packages_data(service)
    ga_utils.save_packages_data(packages_data)
    log.info("Saved %s records from google" % len(packages_data))
