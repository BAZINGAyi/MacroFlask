# Changelog

## Version 0.0.1 - [08-14-2024]

### New Features

Feature 1: Multi-Database / Read-Write Separation Support for MySQL Database.

    - Support Flask or Non-Flask applications.
    - Support Multi-Thread and Multi-Process environments.
    - Support Customized Logger to record Log.
    - Use scoped_session to avoid session conflicts.
    - Support detailed database parameter configuration.

Feature 2: Flexible Permissions Management with Role-Based Access Control.

    - One module can have up to 64 permissions for efficient storage and querying.
    - Use bitwise operations to check and save permissions.

Feature 3: Efficient API registration function, automatically generate regular CURD API to operate the database.

    - Support JWT authentication and permission verification.
    - Automatically generate corresponding API interfaces after generating table structure.
    - Support common Sql query methods, such as paging, nested and or, like ==, !=, etc.
    - Support pydantic Schema validation to ensure api payload is correct.

Feature 4: Detailed Logging Functionality.

    - Rich Log related configuration. For example, Log file size, backup configuration, file name configuration, format configuration, etc.
    - Detailed log output, can trace the entire process from receiving the request to returning the response, which is convenient for troubleshooting.
    - Support Logging record in Multi-Process and Multi-Thread environments.

Feature 5: Rich tools.

    - Linux server, Common Network Device ssh support.
    - Common Multi-Thread tools.
    - OS tools.

### Enhancements

### Bug Fixes

### Technical Updates

### Deprecations

### Known Issues

### Documentation