def is_simple_complex(element: dict) -> str:
    """A function to determine whether the type of element is SimpleType or ComplexType"""
    element_type = element.get("type")
    if element_type == "object":
        return "ComplexType"
    elif element_type == "array":
        return "ArrayType"
    else:
        return "SimpleType"


def check_if_object_has_properties_or_restrictions(element: dict) -> bool:
    if element.get('properties') or element.get('additionalProperties') or element.get('required') or element.get(
            'unevaluatedProperties') or element.get('patternProperties') or element.get(
        'propertyNames') or element.get('dependentRequired'):
        return True
    return False
