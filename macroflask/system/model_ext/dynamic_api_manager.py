import traceback

from flask import request, jsonify, abort, g
from functools import wraps
from flask_jwt_extended import jwt_required

from macroflask.system.logging_producer import LoggingProducer
from macroflask.system.rest_mgmt import permission_required, ResponseHandler
from macroflask.util.os_util import UUIDUtil


class DynamicBlueprintManager:
    def __init__(self, blueprint, model, config):
        self.blueprint = blueprint
        self.model = model
        self.config = config
        self._register_routes()

    def _register_routes(self):
        if self.config.get('create', False):
            self._add_route('create', methods=['POST'])
        if self.config.get('read_all', False):
            self._add_route('read_all', methods=['POST'])
        if self.config.get('read_one', False):
            self._add_route('read_one', methods=['GET'], detail=True)
        if self.config.get('update', False):
            self._add_route('update', methods=['PUT'], detail=True)
        if self.config.get('delete', False):
            self._add_route('delete', methods=['DELETE'], detail=True)

    def _add_route(self, action, methods, detail=False):
        view_func = self._get_view_func(action)
        lower_model_name = self.model.__name__.lower()
        route = f"/{lower_model_name}/" + action + "/"
        if detail:
            route += "<int:id>/"
        endpoint = f"{lower_model_name}_{action}"
        self.blueprint.add_url_rule(
            route, view_func=view_func, methods=methods, endpoint=endpoint, strict_slashes=False)

    def _get_view_func(self, action):
        module_id = self.config['module_id']
        permission_bitmask = self.config[action]['permission_bitmask']

        @jwt_required()
        @permission_required(module_id=module_id, permission_bitmask=permission_bitmask)
        def view_func(*args, **kwargs):
            uuid = g.req_uuid if hasattr(g, 'req_uuid') else UUIDUtil.generate_uuid()
            if action == 'create':
                return self._create(uuid=uuid)
            elif action == 'read_all':
                return self._read_all(uuid=uuid)
            elif action == 'read_one':
                return self._read_one(kwargs['id'], uuid=uuid)
            elif action == 'update':
                return self._update(kwargs['id'], uuid=uuid)
            elif action == 'delete':
                return self._delete(kwargs['id'], uuid=uuid)
            else:
                ResponseHandler.error("Invalid action")

        return view_func

    def _create(self, **kwargs):
        LoggingProducer.log_entrypoint(kwargs, "create")
        data = request.json
        error_msg = None

        try:
            data = self.model.create(data, **kwargs)
        except Exception as e:
            info = traceback.format_exc()
            LoggingProducer.log_error(kwargs, info)
            error_msg = ResponseHandler.convert_error_msg(e)

        LoggingProducer.log_end(kwargs)
        if error_msg:
            return ResponseHandler.error(error_msg)
        return ResponseHandler.success("success_create", data=data)

    def _read_all(self, **kwargs):
        query_result = []
        status = True
        msg = "success_access"

        try:
            query_result = self.model.read_all(request.json)
        except Exception as e:
            status = False
            msg = str(e)

        if not status:
            return ResponseHandler.error(msg)
        return ResponseHandler.success(msg, data=query_result)

    def _read_one(self, id, **kwargs):
        data = self.model.read_one(id)
        return ResponseHandler.success("success_access", data=data)

    def _update(self, id, **kwargs):
        LoggingProducer.log_entrypoint(kwargs, "update")
        msg_error = None

        try:
            data = self.model.update(id, request.json, **kwargs)
        except Exception as e:
            msg_error = ResponseHandler.convert_error_msg(e)
            info = traceback.format_exc()
            LoggingProducer.log_error(kwargs, info)

        LoggingProducer.log_end(kwargs)
        if msg_error:
            return ResponseHandler.error(msg_error)
        return ResponseHandler.success("success_update", data=data)

    def _delete(self, id, **kwargs):
        LoggingProducer.log_entrypoint(kwargs, "delete")
        error_msg = None

        try:
            removed_data = self.model.delete(id, **kwargs)
        except Exception as e:
            info = traceback.format_exc()
            LoggingProducer.log_error(kwargs, info)
            error_msg = ResponseHandler.convert_error_msg(e)
        LoggingProducer.log_end(kwargs)

        if error_msg:
            return ResponseHandler.error(error_msg)
        return ResponseHandler.success("success_delete", data=removed_data)
