"""Tool registry & decorator utilities.

Supports registering python callables as AI-executable tools with
pydantic based argument validation and JSON schema export for model
provider function/tool calling.
"""
from __future__ import annotations

from typing import Callable, Any, Dict, List, Optional, get_type_hints
from pydantic import BaseModel, ValidationError, create_model
import inspect


class ToolSpec(BaseModel):
    name: str
    description: str
    param_schema: Dict[str, Any]


class RegisteredTool(BaseModel):
    spec: ToolSpec
    func: Callable[..., Any]
    model: type[BaseModel]


_REGISTRY: Dict[str, RegisteredTool] = {}


def register_tool(name: Optional[str] = None, description: str = ""):
    def decorator(fn: Callable[..., Any]):
        tool_name = name or fn.__name__
        if tool_name in _REGISTRY:
            raise ValueError(f"Tool already registered: {tool_name}")
        sig = inspect.signature(fn)
        fields = {}
        hints = get_type_hints(fn)
        for param in sig.parameters.values():
            if param.kind in (param.VAR_KEYWORD, param.VAR_POSITIONAL):
                continue
            ann = hints.get(param.name, Any)
            default = ... if param.default is inspect._empty else param.default
            fields[param.name] = (ann, default)
        Model = create_model(f"Tool_{tool_name}_Model", **fields)  # type: ignore
        schema = Model.schema()
        spec = ToolSpec(
            name=tool_name,
            description=description or fn.__doc__ or "",
            param_schema=schema.get("properties", {}),
        )
        _REGISTRY[tool_name] = RegisteredTool(spec=spec, func=fn, model=Model)
        return fn

    return decorator


def get_schema() -> List[Dict[str, Any]]:
    out = []
    for rt in _REGISTRY.values():
        out.append(
            {
                "name": rt.spec.name,
                "description": rt.spec.description,
                "parameters": {
                    "type": "object",
                    "properties": rt.spec.param_schema,
                    "required": [k for k, v in rt.model.schema().get("properties", {}).items() if k in rt.model.__fields__ and not rt.model.__fields__[k].required is False],
                },
            }
        )
    return out


def execute_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if name not in _REGISTRY:
        raise ValueError(f"Unknown tool: {name}")
    rt = _REGISTRY[name]
    try:
        model_instance = rt.model(**arguments)
    except ValidationError as e:
        return {"error": "validation_error", "details": e.errors()}
    try:
        result = rt.func(**model_instance.dict())
    except Exception as e:  # tool runtime failure
        return {"error": "execution_error", "message": str(e)}
    if isinstance(result, dict):
        return result
    return {"result": result}


__all__ = ["register_tool", "get_schema", "execute_tool"]
