from flask import request, jsonify, abort
from functools import wraps
from flask_jwt_extended import jwt_required
from macroflask import db
from macroflask.system.rest_mgmt import permission_required, ResponseHandler
from macroflask.util.query_processor import QueryRequest, QueryProcessor


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
        print(route, methods[0])
        if detail:
            route += "<int:id>/"
        endpoint = f"{lower_model_name}_{action}"
        print(endpoint)
        self.blueprint.add_url_rule(
            route, view_func=view_func, methods=methods, endpoint=endpoint, strict_slashes=False)

    def _get_view_func(self, action):
        module_id = self.config['module_id']
        permission_bitmask = self.config[action]['permission_bitmask']

        @jwt_required()
        @permission_required(module_id=module_id, permission_bitmask=permission_bitmask)
        def view_func(*args, **kwargs):
            if action == 'create':
                return self._create()
            elif action == 'read_all':
                return self._read_all()
            elif action == 'read_one':
                return self._read_one(kwargs['id'])
            elif action == 'update':
                return self._update(kwargs['id'])
            elif action == 'delete':
                return self._delete(kwargs['id'])
            else:
                ResponseHandler.error("Invalid action")

        return view_func

    def _create(self):
        print(self._create.__name__)
        data = request.json
        instance = self.model(**data)
        with db.get_db_session() as session:
            session.add(instance)
        return ResponseHandler.success("success_create", data=instance.to_dict())

    def _read_all(self):
        query_result = []
        status = True
        msg = "success_access"

        try:
            with db.get_db_session() as session:
                body = request.json
                query_request = QueryRequest(body)
                query_processor = QueryProcessor(self.model, session, None, query_request)
                query_result = query_processor.process()
        except Exception as e:
            status = False
            msg = str(e)

        if not status:
            return ResponseHandler.error(msg)
        return ResponseHandler.success(msg, data=query_result)

    def _read_one(self, id):
        print(self._read_one.__name__)
        with db.get_db_session() as session:
            instance = session.query(self.model).get(id)
            if instance is None:
                return ResponseHandler.error("Not found")
        return ResponseHandler.success("success_access", data=instance.to_dict())

    def _update(self, id):
        data = request.json
        with db.get_db_session() as session:
            instance = session.query(self.model).get(id)
            if instance is None:
                return ResponseHandler.error("Not found")

            for key, value in data.items():
                setattr(instance, key, value)
            session.commit()
        return ResponseHandler.success("success_update", data=instance.to_dict())

    def _delete(self, id):
        with db.get_db_session() as session:
            instance = session.query(self.model).get(id)
            if instance is None:
                return ResponseHandler.error("Not found")
            session.delete(instance)
            session.commit()
        return ResponseHandler.success("success_delete")
