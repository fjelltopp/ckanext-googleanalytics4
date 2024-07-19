# -*- coding: utf-8 -*-

import threading
import requests
import logging
import json
import ast

from ckanext.googleanalytics.actions import resource_stat , package_stat, download_package_stat
from ckanext.googleanalytics.plugin.flask_plugin import GAMixinPlugin
import ckanext.googleanalytics.helpers as googleanalytics_helpers
from six.moves.urllib.parse import urlencode
import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h
import ckan.plugins as p


DEFAULT_RESOURCE_URL_TAG = "/downloads/"

log = logging.getLogger(__name__)


class GoogleAnalyticsException(Exception):
    pass


class AnalyticsPostThread(threading.Thread):
    """Threaded Url POST"""

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            data = self.queue.get()
            log.debug("Sending API event to Google Analytics: GA4")
            measure_id = tk.config.get("googleanalytics.measurement_id")
            api_secret = tk.config.get("googleanalytics.api_secret")
            res = requests.post(
                "https://www.google-analytics.com/mp/collect?measurement_id={}&api_secret={}".format(measure_id, api_secret),
                data=json.dumps(data),
                timeout=10,
            )
            self.queue.task_done()


class GoogleAnalyticsPlugin(GAMixinPlugin, p.SingletonPlugin):
    p.implements(p.IConfigurable)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IActions)

    def get_actions(self):
        return {
            'resource_stats': resource_stat,
            'package_stats': package_stat,
            'download_package_stats': download_package_stat
        }

    def configure(self, config):
        """Load config settings for this extension from config file.

        See IConfigurable.

        """
        if "googleanalytics.measurement_id" not in config:
            msg = "Missing googleanalytics.measurement_id in config. One must be set."
            raise GoogleAnalyticsException(msg)
        # TODO: Do we still need to submit `gogleanalytics_id` separately?
        self.googleanalytics_id = config.get('googleanalytics.measurement_id')
        self.googleanalytics_domain = config.get(
            "googleanalytics.domain", "auto"
        )
        self.googleanalytics_fields = ast.literal_eval(
            config.get("googleanalytics.fields", "{}")
        )

        googleanalytics_linked_domains = config.get(
            "googleanalytics.linked_domains", ""
        )
        self.googleanalytics_linked_domains = [
            x.strip() for x in googleanalytics_linked_domains.split(",") if x
        ]

        if self.googleanalytics_linked_domains:
            self.googleanalytics_fields["allowLinker"] = "true"

        # If resource_prefix is not in config file then write the default value
        # to the config dict, otherwise templates seem to get 'true' when they
        # try to read resource_prefix from config.
        if "googleanalytics_resource_prefix" not in config:
            config[
                "googleanalytics_resource_prefix"
            ] = DEFAULT_RESOURCE_URL_TAG
        self.googleanalytics_resource_prefix = config[
            "googleanalytics_resource_prefix"
        ]

        self.show_downloads = tk.asbool(
            config.get("googleanalytics.show_downloads", True)
        )
        self.track_events = tk.asbool(
            config.get("googleanalytics.track_events", False)
        )
        self.enable_user_id = tk.asbool(
            config.get("googleanalytics.enable_user_id", False)
        )

        self.googleanalytics_measurment_id = config.get(
            "googleanalytics.measurement_id", ""
        )

        # p.toolkit.add_resource("../assets", "ckanext-googleanalytics")

        # spawn a pool of 5 threads, and pass them queue instance
        for i in range(5):
            t = AnalyticsPostThread(self.analytics_queue)
            t.setDaemon(True)
            t.start()

    def update_config(self, config):
        """Change the CKAN (Pylons) environment configuration.

        See IConfigurer.

        """
        p.toolkit.add_template_directory(config, "../templates")
        p.toolkit.add_resource('../assets', 'ckanext-googleanalytics')

    def get_helpers(self):
        """Return the CKAN 2.0 template helper functions this plugin provides.

        See ITemplateHelpers.

        """
        return {
            "googleanalytics_header": self.googleanalytics_header,
            'get_package_stats': googleanalytics_helpers.get_package_stats,
            'get_resource_stats': googleanalytics_helpers.get_resource_stats
        }

    def googleanalytics_header(self):
        """Render the googleanalytics_header snippet for CKAN 2.0 templates.

        This is a template helper function that renders the
        googleanalytics_header jinja snippet. To be called from the jinja
        templates in this extension, see ITemplateHelpers.

        """
        try:
            current_user = tk.c.user
        except AttributeError:
            current_user = False

        if self.enable_user_id and current_user:
            self.googleanalytics_fields["userId"] = str(tk.c.userobj.id)

        ## annonymize IP
        self.googleanalytics_fields["anonymize_ip"] = "true"
        data = {
            "googleanalytics_id": self.googleanalytics_id,
            "googleanalytics_domain": self.googleanalytics_domain,
            "googleanalytics_fields": str(self.googleanalytics_fields),
            "googleanalytics_linked_domains": self.googleanalytics_linked_domains,
            "googleanalytics_measurement_id": self.googleanalytics_measurment_id
        }
        return p.toolkit.render_snippet(
            "googleanalytics/snippets/googleanalytics_header.html", data
        )
