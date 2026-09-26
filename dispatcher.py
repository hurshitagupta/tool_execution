import time
from typing import Callable, Any


ToolRegistry = dict[str, Callable[[dict], Any]]


def validate_request(name: str, args: dict) -> None:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Tool name must be a non-empty string")

    if not isinstance(args, dict):
        raise ValueError("Tool arguments must be a dictionary")


def execute_tool(registry: ToolRegistry, name: str, args: dict) -> dict:

    started = time.perf_counter()

    trace = [{
            "event": "dispatch_started",
            "tool": name}]

    try:
        validate_request(name, args)
    except ValueError as exc:
        trace.append({
                "event": "dispatch_rejected",
                "reason": "invalid_request"})

        return {
            "status": "rejected",
            "error": "invalid_request",
            "message": str(exc),
            "trace": trace}

    if name not in registry:
        trace.append({
                "event": "dispatch_rejected",
                "reason": "tool_not_allowed"})

        return {
            "status": "rejected",
            "error": "tool_not_allowed",
            "trace": trace}

    trace.append({
            "event": "tool_selected",
            "tool": name})

    try:
        output = registry[name](args)

        duration_s = time.perf_counter() - started

        trace.append({
                "event": "execution_completed",
                "tool": name})

        return {
            "status": "success",
            "output": output,
            "duration_s": round(duration_s, 6),
            "trace": trace}

    except Exception as exc:
        duration_s = time.perf_counter() - started

        trace.append({
                "event": "execution_failed",
                "tool": name,
                "error": type(exc).__name__})

        return {
            "status": "error",
            "error": type(exc).__name__,
            "duration_s": round(duration_s, 6),
            "trace": trace}

def echo_tool(args: dict) -> str:
    text = args.get("text")

    if not isinstance(text, str):
        raise ValueError("text must be a string")

    return text


def add_tool(args: dict) -> float:
    a = args.get("a")
    b = args.get("b")

    if not isinstance(a, (int, float)):
        raise ValueError("a must be a number")

    if not isinstance(b, (int, float)):
        raise ValueError("b must be a number")

    return a + b


if __name__ == "__main__":

    registry = {
        "echo": echo_tool,
        "add": add_tool}

    print("=== DISPATCHER DEMO ===")

    print("\n1. Successful dispatch")

    success = execute_tool(registry, "echo", {"text": "Hello from dispatcher"})

    print(success)

    print("\n2. Rejected dispatch")

    rejected = execute_tool( registry, "delete_database", {})

    print(rejected)