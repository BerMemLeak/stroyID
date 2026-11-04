"""Validate current card fields without retaining an earlier card payload."""


def describe(value):
    if isinstance(value, dict):
        return {key: describe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [describe(value[0])] if value else []
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, str):
        return "str"
    if isinstance(value, (int, float)):
        return "number"
    return "any"


def check(value, schema, path="Карточка", required=True):
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            raise ValueError("Поле " + path + " должно быть объектом")
        for key, child in schema.items():
            if key not in value:
                if required:
                    raise ValueError("Нет поля " + path + "." + key)
                continue
            check(value[key], child, path + "." + key, required=False)
    elif isinstance(schema, list):
        if not isinstance(value, list):
            raise ValueError("Поле " + path + " должно быть списком")
        # List rows can have optional fields; validate only the shared shape.
        if schema:
            for item in value:
                child = schema[0]
                if isinstance(child, dict) and isinstance(item, dict):
                    child = {k: v for k, v in child.items() if k in item}
                check(item, child, path + "[]", required=False)
    elif schema == "str" and not isinstance(value, str):
        raise ValueError("Поле " + path + " должно быть строкой")
    elif schema == "number" and (isinstance(value, bool) or not isinstance(value, (int, float))):
        raise ValueError("Поле " + path + " должно быть числом")
    elif schema == "bool" and not isinstance(value, bool):
        raise ValueError("Поле " + path + " должно быть логическим")


def defaults(schema):
    if isinstance(schema, dict):
        return {k: defaults(v) for k, v in schema.items()}
    if isinstance(schema, list):
        return []
    return {"str": "", "bool": False, "number": 0}.get(schema)
