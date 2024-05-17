def BUILD_IN_TYPES(json_type):
    type_map = {
        "string": "string",
        "number": "decimal",
        "integer": "integer",
        "boolean": "boolean",
        "null": "nil"
    }
    return type_map.get(json_type, None)


def FORMAT_TYPES(format_type):
    format_type_map = {
        "date-time": "dateTime ",
        "date": "date",
        "time": "time",
        "duration": "duration"
    }
    return format_type_map.get(format_type, None)
