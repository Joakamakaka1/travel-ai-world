"""Derive the all-optional PATCH body from a base schema.

A sent field keeps the base's type and constraints (`FieldInfo.metadata`), so PATCH
refuses what POST refuses: a value let through would fail every later read.
"""

from typing import Annotated, Any

from pydantic import BaseModel, create_model


def partial[T: BaseModel](base: type[T], name: str) -> type[BaseModel]:
    fields: dict[str, Any] = {}
    for field, info in base.model_fields.items():
        annotation = info.annotation
        if annotation is None:
            continue
        if info.metadata:
            annotation = Annotated[annotation, *info.metadata]
        fields[field] = (annotation, None)
    return create_model(name, __doc__=f"Partial update of {base.__name__}.", **fields)
