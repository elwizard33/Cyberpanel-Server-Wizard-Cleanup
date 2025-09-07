"""Tool registry for cyberzard."""

from typing import Dict, Any, Callable, List


# Registry of available tools
TOOL_REGISTRY: Dict[str, Callable] = {}


def register_tool(name: str):
    """Decorator to register a tool."""
    def decorator(func: Callable):
        TOOL_REGISTRY[name] = func
        return func
    return decorator


def execute_tool(tool_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute a registered tool."""
    if tool_name not in TOOL_REGISTRY:
        return {
            "error": f"Tool '{tool_name}' not found",
            "available_tools": list(TOOL_REGISTRY.keys())
        }
    
    try:
        if params is None:
            params = {}
        result = TOOL_REGISTRY[tool_name](**params)
        
        # Handle special cases where tools return status at result level
        if tool_name in ["sandbox_run", "execute_remediation"] and isinstance(result, dict):
            if "error" in result:
                return result
            elif "status" in result:
                # Also return some fields at top level for compatibility
                response = result.copy()
                if tool_name == "sandbox_run" and "returncode" in result:
                    response["returncode"] = result["returncode"]
                return response
        
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_schema(tool_name: str = None) -> Dict[str, Any]:
    """Get schema for a tool or all tools."""
    if tool_name is None:
        # Return all tool schemas
        return [
            {
                "name": name,
                "description": f"Schema for {name}",
                "parameters": {}
            }
            for name in TOOL_REGISTRY.keys()
        ]
    
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Tool '{tool_name}' not found"}
    
    # Basic schema - in a real implementation, this would be more detailed
    return {
        "name": tool_name,
        "description": f"Schema for {tool_name}",
        "parameters": {}
    }


# Example tool registration
@register_tool("example_tool")
def example_tool(message: str = "Hello") -> str:
    """Example tool for testing."""
    return f"Tool says: {message}"


@register_tool("read_file")
def read_file(path: str) -> Dict[str, Any]:
    """Read a file."""
    try:
        from pathlib import Path
        content = Path(path).read_text()
        return {"content": content, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@register_tool("list_dir")
def list_dir(path: str) -> Dict[str, Any]:
    """List directory contents."""
    try:
        from pathlib import Path
        items = [item.name for item in Path(path).iterdir()]
        return {"items": items, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@register_tool("run_scan")
def run_scan(target: str = None) -> Dict[str, Any]:
    """Run a security scan."""
    return {
        "target": target or "default",
        "findings": [],
        "status": "completed"
    }


@register_tool("sandbox_run")
def sandbox_run(source: str) -> Dict[str, Any]:
    """Sandbox execution tool."""
    # Simple security check
    if "import os" in source:
        return {"error": "Import of 'os' not allowed in sandbox", "status": "blocked"}
    
    try:
        # In a real implementation, this would be properly sandboxed
        if "print(" in source:
            # Handle print statements
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                exec(source)
            output = f.getvalue().strip()
            return {"stdout": output, "output": output, "returncode": 0, "status": "success"}
        else:
            result = eval(source) if source.strip() else None
            return {"result": result, "returncode": 0, "status": "success"}
    except Exception as e:
        return {"error": str(e), "returncode": 1, "status": "failed"}


@register_tool("execute_remediation")
def execute_remediation(action: str, target: str, dry_run: bool = False) -> Dict[str, Any]:
    """Execute a remediation action."""
    if dry_run:
        if action == "remove":
            return {"status": "would_remove", "target": target}
        elif action == "kill":
            return {"status": "would_kill", "target": target}
        else:
            return {"status": f"would_{action}", "target": target}
    
    # In a real implementation, this would perform the actual action
    if action == "remove":
        return {"status": "removed", "target": target}
    elif action == "kill":
        return {"status": "killed", "target": target}
    else:
        return {"status": "completed", "target": target}
