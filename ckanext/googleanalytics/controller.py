from __future__ import absolute_import
import hashlib
import logging

from ckan.lib.base import BaseController, c, render, request
from ckan.exceptions import CkanVersionException
from ckan.controllers.api import ApiController
from paste.util.multidict import MultiDict
import ckan.plugins.toolkit as tk
from utils import db as db_utils
import ckan.logic as logic
from pylons import config
from . import plugin

try:
    tk.requires_ckan_version("2.9")
except CkanVersionException:
    pass
else:
    from builtins import str

log = logging.getLogger("ckanext.googleanalytics")


class GAController(BaseController):
    def view(self):
        # get package objects corresponding to popular GA content
        c.top_resources = db_utils.get_top_resources(limit=10)
        return render("summary.html")


class GAApiController(ApiController):
    # intercept API calls to record via google analytics
    def _post_analytics(
        self, user, request_obj_type, request_function, request_id
    ):
        if config.get("googleanalytics.id"):
            data_dict = {
                "v": 1,
                "tid": config.get("googleanalytics.id"),
                "cid": hashlib.md5(user).hexdigest(),
                # customer id should be obfuscated
                "t": "event",
                "dh": c.environ["HTTP_HOST"],
                "dp": c.environ["PATH_INFO"],
                "dr": c.environ.get("HTTP_REFERER", ""),
                "ec": "CKAN API Request",
                "ea": request_obj_type + request_function,
                "el": request_id,
            }
            plugin.GoogleAnalyticsPlugin.analytics_queue.put(data_dict)

    def action(self, logic_function, ver=None):
        try:
            function = logic.get_action(logic_function)
            side_effect_free = getattr(function, "side_effect_free", False)
            request_data = self._get_request_data(
                try_url_params=side_effect_free
            )
            if isinstance(request_data, dict):
                id = request_data.get("id", "")
                if "q" in request_data:
                    id = request_data["q"]
                if "query" in request_data:
                    id = request_data["query"]
                self._post_analytics(c.user, logic_function, "", id)
        except Exception as e:
            log.debug(e)
            pass
        return ApiController.action(self, logic_function, ver)

    def list(self, ver=None, register=None, subregister=None, id=None):
        self._post_analytics(
            c.user,
            register + ("_" + str(subregister) if subregister else ""),
            "list",
            id,
        )
        return ApiController.list(self, ver, register, subregister, id)

    def show(
        self, ver=None, register=None, subregister=None, id=None, id2=None
    ):
        self._post_analytics(
            c.user,
            register + ("_" + str(subregister) if subregister else ""),
            "show",
            id,
        )
        return ApiController.show(self, ver, register, subregister, id, id2)

    def update(
        self, ver=None, register=None, subregister=None, id=None, id2=None
    ):
        self._post_analytics(
            c.user,
            register + ("_" + str(subregister) if subregister else ""),
            "update",
            id,
        )
        return ApiController.update(self, ver, register, subregister, id, id2)

    def delete(
        self, ver=None, register=None, subregister=None, id=None, id2=None
    ):
        self._post_analytics(
            c.user,
            register + ("_" + str(subregister) if subregister else ""),
            "delete",
            id,
        )
        return ApiController.delete(self, ver, register, subregister, id, id2)

    def search(self, ver=None, register=None):
        id = None
        try:
            params = MultiDict(self._get_search_params(request.params))
            if "q" in list(params.keys()):
                id = params["q"]
            if "query" in list(params.keys()):
                id = params["query"]
        except ValueError as e:
            log.debug(str(e))
            pass
        self._post_analytics(c.user, register, "search", id)

        return ApiController.search(self, ver, register)
