"""Condition tree validation and evaluation utilities for rules."""

from typing import Any, get_args, get_origin

from pydantic import BaseModel

from src.audits.schemas import AuditData


def _get_nested_value(obj: dict, path: str) -> Any:
    """Get nested value from object using dot notation."""
    keys = path.split(".")
    value = obj
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
        if value is None:
            return None
    return value


def _evaluate_operator(operator: str, actual: Any, expected: str) -> bool:
    """Evaluate a single operator condition."""
    if operator == "exists":
        return actual is not None

    if actual is None:
        return False

    if operator == "equals":
        return str(actual) == str(expected)
    elif operator == "not equals":
        return str(actual) != str(expected)
    elif operator == "contains":
        return str(expected) in str(actual)
    elif operator == ">=":
        try:
            return float(actual) >= float(expected)
        except (ValueError, TypeError):
            return False
    elif operator == "<=":
        try:
            return float(actual) <= float(expected)
        except (ValueError, TypeError):
            return False
    elif operator == "Is":
        return str(actual).lower() == str(expected).lower()
    else:
        return False


def _validate_condition_node(node: dict) -> list[str]:
    """Validate a single condition node structure."""
    errors: list[str] = []

    if node.get("type") != "condition":
        errors.append("Condition node must have type 'condition'")
        return errors

    required_fields = ["id", "fieldPath", "operator", "value", "fieldType"]
    for field in required_fields:
        if field not in node:
            errors.append(f"Condition node missing required field: {field}")

    if "fieldPath" in node and not isinstance(node["fieldPath"], str):
        errors.append("fieldPath must be a string")

    if "operator" in node:
        valid_operators = ["equals", "not equals", "contains", ">=", "<=", "Is", "exists"]
        if node["operator"] not in valid_operators:
            errors.append(f"Invalid operator: {node['operator']}")

    if "fieldType" in node:
        valid_types = ["string", "number", "boolean", "enum"]
        if node["fieldType"] not in valid_types:
            errors.append(f"Invalid fieldType: {node['fieldType']}")

    return errors


def _validate_group_node(node: dict) -> list[str]:
    """Validate a single group node structure."""
    errors: list[str] = []

    if node.get("type") != "group":
        errors.append("Group node must have type 'group'")
        return errors

    if "id" not in node:
        errors.append("Group node missing required field: id")

    if "logical" not in node:
        errors.append("Group node missing required field: logical")
    elif node["logical"] not in ["AND", "OR"]:
        errors.append("Group logical must be 'AND' or 'OR'")

    if "children" not in node:
        errors.append("Group node missing required field: children")
    elif not isinstance(node["children"], list):
        errors.append("Group children must be an array")
    elif len(node["children"]) == 0:
        errors.append("Group must have at least one child")

    return errors


def validate_condition_tree(condition_tree: dict) -> tuple[bool, list[str]]:
    """
    Validate condition tree structure.

    Returns (valid, errors)
    """
    errors: list[str] = []

    if not isinstance(condition_tree, dict):
        errors.append("Condition tree must be an object")
        return False, errors

    if condition_tree.get("type") != "group":
        errors.append("Root node must be a group node with type 'group'")
        return False, errors

    # Validate root group
    group_errors = _validate_group_node(condition_tree)
    errors.extend(group_errors)

    # Check for empty children at root level
    if "children" in condition_tree and isinstance(condition_tree["children"], list):
        if len(condition_tree["children"]) == 0:
            errors.append("Root group must have at least one child")

    # Recursively validate children
    if "children" in condition_tree and isinstance(condition_tree["children"], list):
        for child in condition_tree["children"]:
            if not isinstance(child, dict):
                errors.append("Child nodes must be objects")
                continue

            child_type = child.get("type")
            if child_type == "group":
                child_errors = _validate_group_node(child)
                errors.extend(child_errors)
                # Recursively validate nested children
                if "children" in child:
                    for nested_child in child["children"]:
                        if isinstance(nested_child, dict):
                            nested_type = nested_child.get("type")
                            if nested_type == "group":
                                nested_valid, nested_errors = validate_condition_tree(nested_child)
                                if not nested_valid:
                                    errors.extend(nested_errors)
                            elif nested_type == "condition":
                                cond_errors = _validate_condition_node(nested_child)
                                errors.extend(cond_errors)
            elif child_type == "condition":
                cond_errors = _validate_condition_node(child)
                errors.extend(cond_errors)
            else:
                errors.append(f"Unknown node type: {child_type}")

    return len(errors) == 0, errors


def evaluate_condition_tree(condition_tree: dict, audit_data: dict[str, Any]) -> bool:
    """
    Evaluate condition tree against audit data.

    Returns True if conditions match, False otherwise.
    """
    if condition_tree.get("type") == "group":
        logical = condition_tree.get("logical", "AND")
        children = condition_tree.get("children", [])

        if logical == "AND":
            return all(evaluate_condition_tree(child, audit_data) for child in children)
        else:  # OR
            return any(evaluate_condition_tree(child, audit_data) for child in children)

    elif condition_tree.get("type") == "condition":
        field_path = condition_tree.get("fieldPath", "")
        operator = condition_tree.get("operator", "")
        expected_value = condition_tree.get("value", "")

        actual_value = _get_nested_value(audit_data, field_path)
        return _evaluate_operator(operator, actual_value, expected_value)

    return False


def validate_and_evaluate_condition_tree(
    condition_tree: dict, audit_data: dict[str, Any] | None = None
) -> tuple[bool, bool | None, list[str]]:
    """
    Validate and evaluate condition tree against audit data.

    Returns (valid, matched, errors)
    """
    valid, errors = validate_condition_tree(condition_tree)

    if not valid:
        return False, None, errors

    if audit_data is None:
        return True, None, []

    try:
        matched = evaluate_condition_tree(condition_tree, audit_data)
        return True, matched, []
    except Exception as err:  # noqa: BLE001
        errors.append(f"Evaluation error: {str(err)}")
        return True, None, errors


def _is_model_type(annotation: Any) -> bool:
    """Check if annotation is a BaseModel subclass."""
    origin = get_origin(annotation) or annotation

    # Handle Union types
    if hasattr(annotation, "__args__"):
        args = get_args(annotation)
        non_none_args = [a for a in args if a is not type(None)]  # noqa: E721
        if non_none_args:
            return _is_model_type(non_none_args[0])

    return isinstance(origin, type) and issubclass(origin, BaseModel)


def _get_base_type(annotation: Any) -> type:
    """Get the base type from annotation, handling Union and Optional."""
    origin = get_origin(annotation) or annotation

    # Handle Union types (including Optional)
    if hasattr(annotation, "__args__"):
        args = get_args(annotation)
        non_none_args = [a for a in args if a is not type(None)]  # noqa: E721
        if non_none_args:
            return _get_base_type(non_none_args[0])

    return origin


def _get_field_type_from_schema(field_info: dict, annotation: Any) -> tuple[str, list[str] | None]:
    """Determine field type and extract enum values from JSON schema."""
    # Check for enum values in JSON schema (from Literal types)
    # Pydantic represents Union[Literal[...], None] as anyOf with enum
    enum_values = field_info.get("enum")
    if not enum_values:
        # Check anyOf for enum (handles Union[Literal[...], None])
        any_of = field_info.get("anyOf", [])
        for option in any_of:
            if "enum" in option:
                enum_values = option.get("enum")
                break

    if enum_values and all(isinstance(v, str) for v in enum_values):
        return "enum", enum_values

    # Check JSON schema type
    json_type = field_info.get("type")
    if json_type == "boolean":
        return "boolean", None
    elif json_type == "number" or json_type == "integer":
        return "number", None
    elif json_type == "string":
        return "string", None

    # Check anyOf for type (handles Union types)
    if not json_type:
        any_of = field_info.get("anyOf", [])
        for option in any_of:
            if option.get("type") != "null":  # Skip null option
                json_type = option.get("type")
                break

    if json_type == "boolean":
        return "boolean", None
    elif json_type in ("number", "integer"):
        return "number", None
    elif json_type == "string":
        return "string", None

    # Fallback to annotation-based inference
    base_type = _get_base_type(annotation)

    if base_type is bool:
        return "boolean", None
    elif base_type in (int, float):
        return "number", None
    elif base_type is str:
        return "string", None
    elif _is_model_type(annotation):
        return "dict", None

    return "string", None  # Default


def _process_model(
    model: type[BaseModel],
    prefix: str = "",
    variables: dict[str, Any] | None = None,
    field_paths: dict[str, Any] | None = None,
) -> None:
    """
    Process a Pydantic model recursively to build variables and field_paths.
    """
    if variables is None:
        variables = {}
    if field_paths is None:
        field_paths = {}

    schema = model.model_json_schema()
    properties = schema.get("properties", {})
    definitions = schema.get("$defs", {})

    # Build fields dict for this model
    model_fields: dict[str, Any] = {}

    # Add to variables if we have a prefix (top-level sections)
    if prefix:
        variables[prefix] = {
            "description": schema.get("description") or (model.__doc__ or "").strip(),
            "type": "dict",
            "fields": model_fields,
        }

    for field_name, field_info in properties.items():
        field_annotation = model.model_fields[field_name].annotation
        field_description = field_info.get("description", "")
        field_ref = field_info.get("$ref")

        # Handle references to nested models
        if field_ref:
            ref_name = field_ref.split("/")[-1]
            if ref_name in definitions:
                ref_schema = definitions[ref_name]
                if "properties" in ref_schema:
                    # It's a nested model - recurse
                    nested_prefix = f"{prefix}.{field_name}" if prefix else field_name
                    nested_model = _get_model_from_ref(ref_name)
                    _process_model(nested_model, nested_prefix, variables, field_paths)
                    model_fields[field_name] = {
                        "type": "dict",
                        "description": field_description,
                    }
                    continue

        # Check if it's a model type directly
        if _is_model_type(field_annotation):
            nested_prefix = f"{prefix}.{field_name}" if prefix else field_name
            nested_model = _get_base_type(field_annotation)
            if isinstance(nested_model, type) and issubclass(nested_model, BaseModel):
                _process_model(nested_model, nested_prefix, variables, field_paths)
                model_fields[field_name] = {
                    "type": "dict",
                    "description": field_description,
                }
                continue

        # Leaf field - determine type
        field_type, enum_values = _get_field_type_from_schema(field_info, field_annotation)

        field_spec: dict[str, Any] = {
            "type": field_type,
            "description": field_description,
        }
        if enum_values:
            field_spec["values"] = enum_values

        model_fields[field_name] = field_spec

        # Add to field_paths (only for leaf fields)
        if field_type != "dict":
            field_path = f"{prefix}.{field_name}" if prefix else field_name
            field_path_spec: dict[str, Any] = {"type": field_type}
            if enum_values:
                field_path_spec["values"] = enum_values
            field_paths[field_path] = field_path_spec


def _get_model_from_ref(ref_name: str) -> type[BaseModel]:
    """Get the model class from a reference name."""
    from src.audits import schemas

    model_map: dict[str, type[BaseModel]] = {
        "ProductInfo": schemas.ProductInfo,
        "Materials": schemas.Materials,
        "Facility": schemas.Facility,
        "Visibility": schemas.Visibility,
        "SupplyChain": schemas.SupplyChain,
        "Environmental": schemas.Environmental,
        "Social": schemas.Social,
        "Circularity": schemas.Circularity,
        "Sustainability": schemas.Sustainability,
        "AuditData": schemas.AuditData,
    }
    model = model_map.get(ref_name)
    if model is None:
        raise ValueError(f"Unknown model reference: {ref_name}")
    return model


def generate_field_catalog() -> dict[str, Any]:
    """
    Generate field catalog from AuditData schema.

    Returns a dictionary with variables, operators, and fieldPaths.
    """
    variables: dict[str, Any] = {
        "audit": {
            "description": "Full audit data object",
            "type": "dict",
        }
    }
    field_paths: dict[str, Any] = {}

    # Process AuditData model recursively
    _process_model(AuditData, "", variables, field_paths)

    # Add operators (these are static, not schema-dependent)
    operators = {
        "string": ["equals", "not equals", "contains", "exists"],
        "number": ["equals", "not equals", ">=", "<=", "exists"],
        "boolean": ["Is", "exists"],
        "enum": ["equals", "not equals", "exists"],
    }

    return {
        "variables": variables,
        "operators": operators,
        "fieldPaths": field_paths,
    }
