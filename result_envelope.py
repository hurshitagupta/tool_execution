import time
from typing import Any, Callable, TypedDict, Optional


class ResultEnvelope(TypedDict):
    status: str
    tool: str
    output: Optional[Any]
    error: Optional[str]
    message: Optional[str]
    duration_s: float
    trace: list[dict]


ToolRegistry = dict[str, Callable[[dict], Any]]


def make_result(*, status: str, tool: str, output: Any = None, error: str | None = None, message: str | None = None, duration_s: float = 0.0, trace: list[dict] | None = None) -> ResultEnvelope:

    return {
        "status": status,
        "tool": tool,
        "output": output,
        "error": error,
        "message": message,
        "duration_s": round(duration_s, 6),
        "trace": trace or [],
    }


def validate_request(name: str, args: dict) -> None:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Tool name must be a non-empty string")

    if not isinstance(args, dict):
        raise ValueError("Tool arguments must be a dictionary")


def execute_tool(registry: ToolRegistry, name: str, args: dict) -> ResultEnvelope:

    started = time.perf_counter()

    trace = [{"event": "execution_started", "tool": name}]

    try:
        validate_request(name, args)

    except ValueError as exc:
        duration_s = time.perf_counter() - started

        trace.append({ "event": "execution_rejected", "reason": "invalid_request"})

        return make_result(status="rejected", tool=name, error="invalid_request", message=str(exc), duration_s=duration_s, trace=trace)

    if name not in registry:
        duration_s = time.perf_counter() - started

        trace.append({ "event": "execution_rejected", "reason": "tool_not_allowed"})

        return make_result(status="rejected", tool=name, error="tool_not_allowed", message="Requested tool is not registered", duration_s=duration_s, trace=trace)

    trace.append({ "event": "tool_selected", "tool": name})

    try:
        output = registry[name](args)

        duration_s = time.perf_counter() - started

        trace.append({ "event": "execution_completed", "tool": name})

        return make_result(status="success", tool=name, output=output, message="Tool executed successfully", duration_s=duration_s, trace=trace)

    except Exception as exc:
        duration_s = time.perf_counter() - started

        trace.append({ "event": "execution_failed", "tool": name, "error": type(exc).__name__})

        return make_result(status="error", tool=name, error=type(exc).__name__, message=str(exc), duration_s=duration_s, trace=trace)


def echo_tool(args: dict) -> str:
    text = args.get("text")

    if not isinstance(text, str):
        raise ValueError("text must be a string")

    return text


def divide_tool(args: dict) -> float:
    a = args.get("a")
    b = args.get("b")

    if not isinstance(a, (int, float)):
        raise ValueError("a must be a number")

    if not isinstance(b, (int, float)):
        raise ValueError("b must be a number")

    return a / b


if __name__ == "__main__":

    registry = { "echo": echo_tool, "divide": divide_tool}

    print("=== RESULT ENVELOPE DEMO ===")

    print("\n1. Success result")

    success = execute_tool(registry, "echo", {"text": "hello"})

    print(success)

    print("\n2. Failure result")

    failure = execute_tool(registry, "divide",{"a": 10, "b": 0,})

    print(failure)

    print("\n3. Rejected result")

    rejected = execute_tool(registry, "unknown_tool",{})

    print(rejected)