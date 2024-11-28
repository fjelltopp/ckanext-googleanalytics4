import queue
import ast

from ckanext.googleanalytics.blueprints import blueprints
from ckanext.googleanalytics.command import get_commands
from ckanext.googleanalytics.logic import AnalyticsPostThread
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.googleanalytics.actions as ga_actions
import ckanext.googleanalytics.helpers as ga_helpers

DEFAULT_RESOURCE_URL_TAG = "/downloads/"


class GoogleAnalyticsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)

    analytics_queue = queue.Queue()

    # IActions
    def get_actions(self):
        return {
            "resource_stats": ga_actions.resource_stat,
            "package_stats": ga_actions.package_stat,
            "url_stats": ga_actions.url_stat,
            "download_package_stats": ga_actions.download_package_stat,
            "download_url_stats": ga_actions.download_url_stat,
        }

    # IBlueprint
    def get_blueprint(self):
        return blueprints

    # IClick
    def get_commands(self):
        return get_commands()

    # IConfigurable
    def configure(self, config):
        if "googleanalytics.measurement_id" not in config:
            raise KeyError(
                "Missing googleanalytics.measurement_id in config. One must be set."
            )
        # TODO: Do we still need to submit `gogleanalytics_id` separately?
        self.googleanalytics_id = config.get("googleanalytics.measurement_id")
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
            config["googleanalytics_resource_prefix"] = (
                DEFAULT_RESOURCE_URL_TAG
            )
        self.googleanalytics_resource_prefix = config[
            "googleanalytics_resource_prefix"
        ]

        self.show_downloads = toolkit.asbool(
            config.get("googleanalytics.show_downloads", True)
        )
        self.track_events = toolkit.asbool(
            config.get("googleanalytics.track_events", False)
        )
        self.enable_user_id = toolkit.asbool(
            config.get("googleanalytics.enable_user_id", False)
        )

        self.googleanalytics_measurment_id = config.get(
            "googleanalytics.measurement_id", ""
        )

        # spawn a pool of 5 threads, and pass them queue instance
        for i in range(5):
            t = AnalyticsPostThread(self.analytics_queue)
            t.setDaemon(True)
            t.start()

    # IConfigurer
    def update_config(self, config):
        plugins.toolkit.add_template_directory(config, "../templates")
        plugins.toolkit.add_resource("../assets", "ckanext-googleanalytics")

    # IPackageController (CKAN <= 2.9)
    # IResourceController (CKAN <= 2.9)
    def after_delete(self, context, data_dict):
        # Make sure to delete package/resource visists when the corresponding package/resource is deleted
        pass

    # IPackageController (CKAN > 2.9)
    def after_dataset_delete(self, context, data_dict):
        # Make sure to delete package visists when the corresponding package is deleted
        pass

    # IResourceController (CKAN > 2.9)
    def after_resource_delete(self, context, data_dict):
        # Make sure to delete resource visists when the corresponding resource is deleted
        pass

    # ITemplateHelpers
    def get_helpers(self):
        return {
            "googleanalytics_header": self._googleanalytics_header,
            "get_package_stats": ga_helpers.get_package_stats,
            "get_resource_stats": ga_helpers.get_resource_stats,
            "get_url_stats": ga_helpers.get_url_stats,
        }

    def _googleanalytics_header(self):
        """Render the googleanalytics_header snippet.

        This is a template helper function that renders the
        googleanalytics_header jinja snippet. To be called from the jinja
        templates in this extension, see ITemplateHelpers.

        """
        try:
            current_user = toolkit.c.user
        except AttributeError:
            current_user = False

        if self.enable_user_id and current_user:
            self.googleanalytics_fields["userId"] = str(toolkit.c.userobj.id)

        self.googleanalytics_fields["anonymize_ip"] = "true"
        data = {
            "googleanalytics_id": self.googleanalytics_id,
            "googleanalytics_domain": self.googleanalytics_domain,
            "googleanalytics_fields": str(self.googleanalytics_fields),
            "googleanalytics_linked_domains": self.googleanalytics_linked_domains,
            "googleanalytics_measurement_id": self.googleanalytics_measurment_id,
        }
        return plugins.toolkit.render_snippet(
            "googleanalytics/snippets/googleanalytics_header.html", data
        )
