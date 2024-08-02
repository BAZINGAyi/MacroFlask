from macroflask.models import db
from macroflask.system.model_ext.query_processor import QueryRequest, QueryProcessor


class ModelExtMixin:
    @classmethod
    def create(cls, data):
        is_replace_data, new_data = cls.before_create(data)
        if is_replace_data:
            data = new_data

        instance = cls(**data)
        with db.get_db_session() as session:
            session.add(instance)
        created_data = instance.to_dict()
        return created_data

    @classmethod
    def read_all(cls, request_body):
        query_result = []
        with db.get_db_session() as session:
            query_request = QueryRequest(request_body)
            query_processor = QueryProcessor(cls, session, None, query_request)
            query_result = query_processor.process()
        return query_result

    @classmethod
    def read_one(cls, id):
        with db.get_db_session() as session:
            instance = session.query(cls).get(id)
        return instance.to_dict()

    @classmethod
    def update(cls, id, data):
        validation_response = cls.before_update(id, data)
        if validation_response:
            return validation_response

        with db.get_db_session() as session:
            instance = session.query(cls).get(id)
            if instance is None:
                raise Exception("Not found instance with id: %s" % id)
            for key, value in data.items():
                setattr(instance, key, value)
        return instance.to_dict()

    @classmethod
    def delete(cls, id):
        with db.get_db_session() as session:
            instance = session.query(cls).get(id)
            if instance is None:
                raise Exception("Not found instance with id: %s" % id)
            session.delete(instance)
        return instance.to_dict()

    @classmethod
    def before_create(cls, data):
        is_replace_data = False
        return is_replace_data, None

    @classmethod
    def before_update(cls, data):
        is_replace_data = False
        return is_replace_data, None
