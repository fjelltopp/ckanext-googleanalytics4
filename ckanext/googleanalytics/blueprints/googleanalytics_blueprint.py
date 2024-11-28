import hashlib
import logging
import six

from ckan.common import g
from flask import Blueprint
from werkzeug.utils import import_string, ImportStringError
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as toolkit
import ckan.views.api as api
import ckan.views.resource as resource

from ckanext.googleanalytics.logic import post_analytics


log = logging.getLogger(__name__)


googleanalytics_blueprint = Blueprint("google_analytics", __name__)


CONFIG_HANDLER_PATH = "googleanalytics.download_handler"


def action(logic_function, ver=api.API_MAX_VERSION):
    try:
        function = logic.get_action(logic_function)
        side_effect_free = getattr(function, "side_effect_free", False)
        request_data = api._get_request_data(try_url_params=side_effect_free)
        if isinstance(request_data, dict):
            id = request_data.get("id", "")
            if "q" in request_data:
                id = request_data["q"]
            if "query" in request_data:
                id = request_data["query"]
            post_analytics(g.user)
    except Exception as e:
        log.debug(e)
        pass

    return api.action(logic_function, ver)


googleanalytics_blueprint.add_url_rule(
    "/api/action/<logic_function>",
    methods=["GET", "POST"],
    view_func=action,
)
googleanalytics_blueprint.add_url_rule(
    "/api/<int(min=1, max={0}):ver>/action/<logic_function>".format(
        api.API_MAX_VERSION
    ),
    methods=["GET", "POST"],
    view_func=action,
)
googleanalytics_blueprint.add_url_rule(
    "/<int(min=3, max={0}):ver>/action/<logic_function>".format(
        api.API_MAX_VERSION
    ),
    methods=["GET", "POST"],
    view_func=action,
)


def download(id, resource_id, filename=None, package_type="dataset"):
    handler_path = toolkit.config.get("googleanalytics.download_handler")
    using_default_handler = False

    if handler_path:
        try:
            download_handler = import_string(handler_path)
        except (ImportError, ImportStringError) as e:
            log.debug("`download_handler` configured but not found")
            raise e
    else:
        log.debug(
            "`download_handler` not configured, using CKAN's default which is: resource.download"
        )
        download_handler = resource.download
        using_default_handler = True

    try:
        post_analytics(g.user)
    except Exception as e:
        log.error(e)

    if using_default_handler:
        return download_handler(
            package_type="dataset",
            id=id,
            resource_id=resource_id,
            filename=filename,
        )
    else:
        return download_handler(
            id=id,
            resource_id=resource_id,
            filename=filename,
        )


googleanalytics_blueprint.add_url_rule(
    "/dataset/<id>/resource/<resource_id>/download", view_func=download
)
googleanalytics_blueprint.add_url_rule(
    "/dataset/<id>/resource/<resource_id>/download/<filename>",
    view_func=download,
)
