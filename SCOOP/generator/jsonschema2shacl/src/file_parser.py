import json


def parse_json_schema(file_path: str) -> dict | None:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            schema = json.load(file)
        return schema
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON file: {e}")
        return None
