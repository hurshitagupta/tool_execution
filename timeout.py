import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Callable, Any


ToolRegistry = dict[str, Callable[[dict], Any]]


def validate_request(name: str, args: dict, timeout_s: float) -> None:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Tool name must be a non-empty string")

    if not isinstance(args, dict):
        raise ValueError("Tool arguments must be a dictionary")

    if not isinstance(timeout_s, (int, float)) or timeout_s <= 0:
        raise ValueError("timeout_s must be greater than 0")


def execute_tool(registry: ToolRegistry, name: str, args: dict, timeout_s: float = 2.0) -> dict:

    started = time.perf_counter()

    trace = [{"event": "dispatch_started", "tool": name}]

    try:
        validate_request(name, args, timeout_s)

    except ValueError as exc:
        trace.append({"event": "dispatch_rejected",
                "reason": "invalid_request"})

        return {
            "status": "rejected",
            "error": "invalid_request",
            "message": str(exc),
            "trace": trace
            }

    if name not in registry:
        trace.append({"event": "dispatch_rejected",
                "reason": "tool_not_allowed"})

        return {
            "status": "rejected",
            "error": "tool_not_allowed",
            "trace": trace
        }

    trace.append({"event": "tool_selected", "tool": name})

    executor = ThreadPoolExecutor(max_workers=1)

    future = executor.submit(registry[name], args)

    try:
        output = future.result(timeout=timeout_s)

        duration_s = time.perf_counter() - started

        trace.append({ "event": "execution_completed", "tool": name})

        executor.shutdown(wait=False)

        return {
            "status": "success",
            "output": output,
            "duration_s": round(duration_s, 6),
            "trace": trace
        }

    except TimeoutError:
        duration_s = time.perf_counter() - started

        trace.append({"event": "execution_timeout", "tool": name})

        future.cancel()
        executor.shutdown(wait=False)

        return {
            "status": "timeout",
            "error": "execution_timeout",
            "timeout_s": timeout_s,
            "duration_s": round(duration_s, 6),
            "trace": trace
        }

    except Exception as exc:
        duration_s = time.perf_counter() - started

        trace.append({ "event": "execution_failed", "tool": name, "error": type(exc).__name__})

        executor.shutdown(wait=False)

        return {
            "status": "error",
            "error": type(exc).__name__,
            "duration_s": round(duration_s, 6),
            "trace": trace
        }


def fast_tool(args: dict) -> str:
    return f"Processed: {args['text']}"


def slow_tool(args: dict) -> str:
    delay = args.get("delay", 2)

    time.sleep(delay)

    return "Slow tool completed"


if __name__ == "__main__":

    registry = {"fast": fast_tool, "slow": slow_tool}

    print("=== TIMEOUT DEMO ===")

    print("\n1. Successful execution")

    success = execute_tool(registry, "fast", {"text": "hello"}, timeout_s=1.0)

    print(success)

    print("\n2. Timeout execution")

    timeout_result = execute_tool(registry, "slow", {"delay": 2}, timeout_s=0.5)

    print(timeout_result)