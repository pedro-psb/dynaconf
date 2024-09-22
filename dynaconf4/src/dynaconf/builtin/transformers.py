import json

builtin_transformers_map = {
    "int": lambda val, ctx: int(val),
    "str": lambda val, ctx: str(val),
    "bool": lambda val, ctx: bool(val),
    "json": lambda val, ctx: json.loads(val),
}
