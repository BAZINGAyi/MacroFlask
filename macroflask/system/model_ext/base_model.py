from macroflask.models import db
from macroflask.system.logging_produce import LoggingProducer
from macroflask.system.model_ext.query_processor import QueryRequest, QueryProcessor


class ModelExtMixin:

    create_schema = None
    update_schema = None

    @classmethod
    def create(cls, data, **kwargs):
        LoggingProducer.log_validate_payload(kwargs, data)
        if cls.create_schema:
            data = cls.create_schema(**data).dict(exclude_unset=True)

        LoggingProducer.log_process_business(kwargs, data)
        is_replace_data, new_data = cls.before_create(data)
        if is_replace_data:
            data = new_data

        LoggingProducer.log_db_save(kwargs, data)
        instance = cls(**data)
        with db.get_db_session() as session:
            session.add(instance)
        created_data = instance.to_dict()
        LoggingProducer.log_save_success(kwargs, created_data)

        return created_data

    @classmethod
    def read_all(cls, request_body, **kwargs):
        with db.get_db_session() as session:
            query_request = QueryRequest(request_body)
            query_processor = QueryProcessor(cls, session, None, query_request)
            query_result = query_processor.process()
        return query_result

    @classmethod
    def read_one(cls, id, **kwargs):
        with db.get_db_session() as session:
            instance = session.query(cls).get(id)
        return instance.to_dict()

    @classmethod
    def update(cls, id, data, **kwargs):
        LoggingProducer.log_validate_payload(kwargs, data)
        if cls.update_schema:
            data = cls.update_schema(**data).dict(exclude_unset=True)

        LoggingProducer.log_process_business(kwargs, data)
        is_replace_data, new_data = cls.before_update(id, data)
        if is_replace_data:
            data = new_data

        LoggingProducer.log_db_save(kwargs, data)
        with db.get_db_session() as session:
            instance = session.query(cls).get(id)
            if instance is None:
                raise Exception("Not found instance with id: %s" % id)
            for key, value in data.items():
                setattr(instance, key, value)
        updated_data = instance.to_dict()
        LoggingProducer.log_save_success(kwargs, updated_data)
        return updated_data

    @classmethod
    def delete(cls, id, **kwargs):
        LoggingProducer.log_save_success(kwargs, id)
        with db.get_db_session() as session:
            instance = session.query(cls).get(id)
            if instance is None:
                raise Exception("Not found instance with id: %s" % id)
            session.delete(instance)
        deleted_data = instance.to_dict()
        LoggingProducer.log_save_success(kwargs, deleted_data)
        return deleted_data

    @classmethod
    def before_create(cls, data, **kwargs):
        is_replace_data = False
        return is_replace_data, None

    @classmethod
    def before_update(cls, data, **kwargs):
        is_replace_data = False
        return is_replace_data, None
