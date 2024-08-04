import json

from macroflask.system.sys_ext.loading_logger import app_logger as logging


class LoggingProducer:
    # Define the log format strings
    ENTRYPOINT_TEMPLATE = "==== {uuid} Start processing {action} data start : {message}"
    VALIDATE_PAYLOAD_TEMPLATE = "++ {uuid} Payload validation start : {message}"
    PROCESS_BUSINESS_TEMPLATE = "++ {uuid} Business processing start : {message}"
    DB_SAVE_TEMPLATE = "++ {uuid} Database save start : {message}"
    SAVE_SUCCESS_TEMPLATE = "++ {uuid} Data saved successfully : {message}"
    LOG_ERROR_TEMPLATE = "!! {uuid} Error occurred : {message}"
    END_TEMPLATE = "=== {uuid} End processing"

    @classmethod
    def convert_to_string(cls, data):
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            return json.dumps(data)
        if isinstance(data, int):
            return str(data)
        else:
            return ""

    @classmethod
    def convert_to_uuid(cls, data):
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            return data['uuid'] if 'uuid' in data else json.dumps(data)
        else:
            return ""

    @classmethod
    def log_entrypoint(cls, uuid, action, message=None):
        message = cls.convert_to_string(message)
        uuid = cls.convert_to_uuid(uuid)
        logging.info(LoggingProducer.ENTRYPOINT_TEMPLATE.format(uuid=uuid, action=action, message=message))

    @classmethod
    def log_validate_payload(cls, uuid, message=None):
        message = cls.convert_to_string(message)
        uuid = cls.convert_to_uuid(uuid)
        logging.info(LoggingProducer.VALIDATE_PAYLOAD_TEMPLATE.format(uuid=uuid, message=message))

    @classmethod
    def log_process_business(cls, uuid, message=None):
        message = cls.convert_to_string(message)
        uuid = cls.convert_to_uuid(uuid)
        logging.info(LoggingProducer.PROCESS_BUSINESS_TEMPLATE.format(uuid=uuid, message=message))

    @classmethod
    def log_db_save(cls, uuid, message=None):
        message = cls.convert_to_string(message)
        uuid = cls.convert_to_uuid(uuid)
        logging.info(LoggingProducer.DB_SAVE_TEMPLATE.format(uuid=uuid, message=message))

    @classmethod
    def log_save_success(cls, uuid, message=None):
        message = cls.convert_to_string(message)
        uuid = cls.convert_to_uuid(uuid)
        logging.info(LoggingProducer.SAVE_SUCCESS_TEMPLATE.format(uuid=uuid, message=message))

    @classmethod
    def log_error(cls, uuid, message=None):
        message = cls.convert_to_string(message)
        uuid = cls.convert_to_uuid(uuid)
        logging.error(LoggingProducer.LOG_ERROR_TEMPLATE.format(uuid=uuid, message=message))

    @classmethod
    def log_end(cls, uuid=None):
        uuid = cls.convert_to_uuid(uuid)
        logging.info(LoggingProducer.END_TEMPLATE.format(uuid=uuid))