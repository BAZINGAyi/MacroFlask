from sqlalchemy import Integer, String, Column, Boolean, ForeignKey, BigInteger
from flask_login import current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from macroflask.models import Base, CommonModelMixin


class User(Base, UserMixin, CommonModelMixin):
    __tablename__ = "sys_user"

    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)  # Store hashed password, not plain text
    is_active = Column(Boolean, default=True)  # Whether the account is active
    phone_number = Column(String(20), nullable=True)
    last_login_time = Column(String(50), nullable=True)
    locale = Column(String(32))
    role_id = Column(Integer, ForeignKey("sys_role.id"), nullable=False)

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        self.set_password(password)

    def set_password(self, password):
        """Generate a hash for the given password and set it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hashed password."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role_id': self.role_id
        }


class Role(Base, CommonModelMixin):
    __tablename__ = "sys_role"

    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Role {self.name}>"


class ModuleConstant:
    USER = 1
    ROLE = 2
    PERMISSION = 3


class Module(Base, CommonModelMixin):
    __tablename__ = "sys_module"

    name = Column(String(50), unique=True, nullable=False)
    url = Column(String(100), nullable=False)
    icon = Column(String(50), nullable=True)
    parent_id = Column(Integer, nullable=True)
    path = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<Module {self.name}>"


class PermissionsConstant:
    READ = 1 << 0
    WRITE = 1 << 1
    DELETE = 1 << 2
    UPDATE = 1 << 3


# Inverse mapping for easier lookup
PERMISSIONS_INV = {v: k for k, v in PermissionsConstant.__dict__.items() if not k.startswith("__")}


class Permission(Base, CommonModelMixin):
    __tablename__ = "sys_permission"

    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<Permission {self.name}>"


class ModulePermission(Base):
    """
        Indicate module can own permissions as template.
    """
    __tablename__ = "sys_module_permission"

    id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(Integer, ForeignKey("sys_module.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("sys_permission.id"), nullable=False)

    def __repr__(self):
        return f"<ModulePermission {self.module_id}-{self.permission_id}>"


class RoleModulePermission(Base):
    __tablename__ = "sys_role_module_permission"

    """
        Indicate role actually has permissions to access module.
        one role can have multiple menus
        one menu can have multiple permissions
        one menu can belong to multiple roles
    """

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("sys_role.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("sys_module.id"), nullable=False)
    # use bit to store permissions
    permissions = Column(BigInteger, nullable=True)

    def __repr__(self):
        return f"<RoleMenu {self.role_id}-{self.module_id}>"

    def set_permission(self, permission_bitmask):
        """
        Set the given permission by its name.

        :param permission_bitmask: The permission bitmask to set.
        """
        if permission_bitmask is not None:
            if self.permissions is None:
                self.permissions = 0
            self.permissions |= permission_bitmask

    def remove_permission(self, permission_bitmask):
        """
        Remove the given permission by its name.

        :param permission_bitmask: The permission bitmask to remove.
        """
        if permission_bitmask is not None and self.permissions is not None:
            self.permissions &= ~permission_bitmask

    def has_permission(self, permission_bitmask):
        """
        Check if the given permission by its name is set.

        :param permission_bitmask: The permission bitmask to check.
        :return: True if the permission is set, False otherwise.
        """
        if permission_bitmask is not None and self.permissions is not None:
            return (self.permissions & permission_bitmask) == permission_bitmask
        return False


class OperationLog(Base, CommonModelMixin):
    __tablename__ = "sys_operation_log"
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("sys_module.id"), nullable=False)

    def __repr__(self):
        return f"<OperationLog {self.user_id}-{self.module_id}>"