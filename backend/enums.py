"""
Shared enumerations for both the database layer (models) and validation layer (schemas).

Centralising enums here ensures a single source of truth — adding a new role
or record type only requires a change in one place.
"""

import enum


class RoleEnum(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class TypeEnum(str, enum.Enum):
    income = "income"
    expense = "expense"
