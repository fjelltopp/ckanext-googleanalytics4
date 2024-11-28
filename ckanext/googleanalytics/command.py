import logging
import click

import ckan.plugins.toolkit as tk
import ckan.model as model
from ckanext.googleanalytics.model import init_tables
from ckanext.googleanalytics.logic import load_package_stats, load_url_stats


log = logging.getLogger(__name__)


def get_commands():
    return [googleanalytics]


@click.group(short_help="GoogleAnalytics commands")
def googleanalytics():
    pass


@googleanalytics.command()
def init():
    """Initialise the local stats database tables"""
    model.Session.remove()
    model.Session.configure(bind=model.meta.engine)
    init_tables()
    log.info("Set up statistics tables in main database")


@googleanalytics.command(short_help="Load data from Google Analytics API")
@click.argument("credentials", type=click.Path(exists=True))
@click.option("-s", "--start-date", required=False)
def load(credentials, start_date):
    """Parse data from Google Analytics API and store it
    in a local database
    """
    # Fetch package and resource download stats from GA and save them locally
    packages_data = load_package_stats(credentials)

    # Fetch url stats from GA and save them locally
    urls_data = load_url_stats(credentials)

    log.info("Saved %s packages visits from google" % len(packages_data))
    log.info("Saved %s urls visits from google" % len(urls_data))
