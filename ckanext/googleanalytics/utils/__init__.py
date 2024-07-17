import re

import ckan.plugins.toolkit as tk


DEFAULT_RESOURCE_URL_TAG    = "/downloads/"
DEFAULT_RECENT_VIEW_DAYS    = 14
RESOURCE_URL_REGEX          = re.compile("(/.*/)dataset/([a-z0-9-_]+)/resource/([a-z0-9-_]+)")
PACKAGE_URL                 = "/dataset/"


def _resource_url_tag():
    return tk.config.get(
        "googleanalytics_resource_prefix", DEFAULT_RESOURCE_URL_TAG
    )


def _recent_view_days():
    return tk.asint(
        tk.config.get(
            "googleanalytics.recent_view_days", DEFAULT_RECENT_VIEW_DAYS
        )
    )