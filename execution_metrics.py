import time
from typing import Callable, Any


ToolRegistry = dict[str, Callable[[dict], Any]]


class ExecutionMetrics:
    def __init__(self):
        self.total_executions = 0
        self.success_count = 0
        self.error_count = 0
        self.rejected_count = 0
        self.total_duration_s = 0.0

    def record(self, status: str, duration_s: float) -> None:
        self.total_executions += 1
        self.total_duration_s += duration_s

        if status == "success":
            self.success_count += 1

        elif status == "error":
            self.error_count += 1

        elif status == "rejected":
            self.rejected_count += 1

    def summary(self) -> dict:
        if self.total_executions == 0:
            average_duration_s = 0.0
            success_rate = 0.0
            error_rate = 0.0
        else:
            average_duration_s = (self.total_duration_s / self.total_executions)

            success_rate = (self.success_count / self.total_executions) * 100

            error_rate = (self.error_count / self.total_executions) * 100

        return {
            "total_executions": self.total_executions,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "rejected_count": self.rejected_count,
            "success_rate_percent": round(success_rate, 2),
            "error_rate_percent": round(error_rate, 2),
            "average_duration_s": round(average_duration_s, 6)
        }


def validate_request(name: str, args: dict) -> None:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Tool name must be a non-empty string")

    if not isinstance(args, dict):
        raise ValueError("Tool arguments must be a dictionary")


def execute_tool(registry: ToolRegistry, name: str, args: dict, metrics: ExecutionMetrics) -> dict:

    started = time.perf_counter()

    trace = [{"event": "execution_started", "tool": name}]

    try:
        validate_request(name, args)

    except ValueError as exc:
        duration_s = time.perf_counter() - started

        metrics.record("rejected", duration_s)

        trace.append({"event": "execution_rejected", "reason": "invalid_request"})

        return {
            "status": "rejected",
            "error": "invalid_request",
            "message": str(exc),
            "duration_s": round(duration_s, 6),
            "trace": trace
        }

    if name not in registry:
        duration_s = time.perf_counter() - started

        metrics.record("rejected", duration_s)

        trace.append({ "event": "execution_rejected", "reason": "tool_not_allowed"})

        return {
            "status": "rejected",
            "error": "tool_not_allowed",
            "duration_s": round(duration_s, 6),
            "trace": trace
        }

    trace.append({"event": "tool_selected", "tool": name})

    try:
        output = registry[name](args)

        duration_s = time.perf_counter() - started

        metrics.record("success", duration_s)

        trace.append({ "event": "execution_completed", "tool": name})

        return {"status": "success", "output": output, "duration_s": round(duration_s, 6), "trace": trace}

    except Exception as exc:
        duration_s = time.perf_counter() - started

        metrics.record("error", duration_s)

        trace.append({"event": "execution_failed", "tool": name, "error": type(exc).__name__})

        return {
            "status": "error",
            "error": type(exc).__name__,
            "duration_s": round(duration_s, 6),
            "trace": trace,
        }


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

    registry = {"echo": echo_tool, "divide": divide_tool}

    metrics = ExecutionMetrics()

    print("=== EXECUTION METRICS DEMO ===")

    print("\n1. Successful execution")

    print(execute_tool(registry, "echo", {"text": "hello"}, metrics))

    print("\n2. Another successful execution")

    print(execute_tool(registry, "divide",{"a": 10, "b": 2}, metrics))

    print("\n3. Failed execution")

    print(execute_tool(registry, "divide",{"a": 10,"b": 0}, metrics))

    print("\n4. Rejected execution")

    print(execute_tool(registry,"unknown_tool", {}, metrics))

    print("\n=== METRICS SUMMARY ===")

    print(metrics.summary())