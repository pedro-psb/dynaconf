from _dynaconf.coreutils.validate import ValidationError


class DynaconfSchemaError(Exception): ...


__all__ = ["DynaconfSchemaError", "ValidationError"]
