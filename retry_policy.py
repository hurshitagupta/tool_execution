import time
from typing import Callable, Any


ToolRegistry = dict[str, Callable[[dict], Any]]


class TransientToolError(Exception):
    """Failure that may succeed if retried."""


class PermanentToolError(Exception):
    """Failure that should not be retried."""


IDEMPOTENCY_STORE: dict[str, Any] = {}


def validate_request(name: str, args: dict, max_retries: int, backoff_s: float) -> None:

    if not isinstance(name, str) or not name.strip():
        raise ValueError("Tool name must be a non-empty string")

    if not isinstance(args, dict):
        raise ValueError("Tool arguments must be a dictionary")

    if not isinstance(max_retries, int) or max_retries < 0:
        raise ValueError("max_retries must be zero or greater")

    if max_retries > 3:
        raise ValueError("max_retries cannot exceed 3")

    if not isinstance(backoff_s, (int, float)) or backoff_s < 0:
        raise ValueError("backoff_s must be zero or greater")


def execute_tool(registry: ToolRegistry, name: str, args: dict, max_retries: int = 2, backoff_s: float = 0.1) -> dict:

    started = time.perf_counter()

    trace = [{"event": "execution_started", "tool": name}]

    try:
        validate_request(name, args, max_retries, backoff_s)

    except ValueError as exc:
        trace.append({"event": "execution_rejected", "reason": "invalid_request"})

        return {
            "status": "rejected",
            "error": "invalid_request",
            "message": str(exc),
            "trace": trace
        }

    if name not in registry:
        trace.append({"event": "execution_rejected", "reason": "tool_not_allowed"})

        return {
            "status": "rejected",
            "error": "tool_not_allowed",
            "trace": trace
        }

    total_attempts = max_retries + 1

    for attempt in range(1, total_attempts + 1):

        trace.append({ "event": "attempt_started", "attempt": attempt})

        try:
            output = registry[name](args)

            duration_s = time.perf_counter() - started

            trace.append({ "event": "execution_completed", "attempt": attempt})

            return {
                "status": "success",
                "output": output,
                "attempts": attempt,
                "retries": attempt - 1,
                "duration_s": round(duration_s, 6),
                "trace": trace
            }

        except TransientToolError as exc:

            trace.append({
                    "event": "transient_failure",
                    "attempt": attempt,
                    "error": type(exc).__name__
                })

            if attempt >= total_attempts:
                duration_s = time.perf_counter() - started

                trace.append({ "event": "retry_limit_reached", "attempt": attempt})

                return {
                    "status": "error",
                    "error": "retry_limit_reached",
                    "attempts": attempt,
                    "retries": attempt - 1,
                    "duration_s": round(duration_s, 6),
                    "trace": trace
                }

            delay = min(backoff_s * attempt, 0.5)

            trace.append({ "event": "retry_scheduled", "next_attempt": attempt + 1, "backoff_s": delay })

            time.sleep(delay)

        except PermanentToolError as exc:

            duration_s = time.perf_counter() - started

            trace.append({"event": "permanent_failure", "attempt": attempt, "error": type(exc).__name__})

            return {
                "status": "error",
                "error": type(exc).__name__,
                "attempts": attempt,
                "retries": attempt - 1,
                "duration_s": round(duration_s, 6),
                "trace": trace
            }

        except Exception as exc:

            duration_s = time.perf_counter() - started

            trace.append({ "event": "unclassified_failure", "attempt": attempt, "error": type(exc).__name__})

            return {
                "status": "error",
                "error": type(exc).__name__,
                "attempts": attempt,
                "retries": attempt - 1,
                "duration_s": round(duration_s, 6),
                "trace": trace
            }

def echo_tool(args: dict) -> str:
    return args["text"]


transient_counter = {"count": 0}


def flaky_tool(args: dict) -> str:
    failures_before_success = args.get("failures_before_success", 1)

    if transient_counter["count"] < failures_before_success:
        transient_counter["count"] += 1

        raise TransientToolError( "Temporary service failure" )

    return "Tool succeeded"


def permanent_failure_tool(args: dict) -> str:
    raise PermanentToolError( "Invalid request cannot be retried" )


def always_transient_tool(args: dict) -> str:
    raise TransientToolError( "Service is temporarily unavailable" )


def create_order_tool(args: dict) -> dict:

    idempotency_key = args.get("idempotency_key")
    order_id = args.get("order_id")

    if not idempotency_key:
        raise PermanentToolError("idempotency_key is required")

    if not order_id:
        raise PermanentToolError("order_id is required")

    if idempotency_key in IDEMPOTENCY_STORE:
        return {"message": "Existing result returned", "order": IDEMPOTENCY_STORE[idempotency_key]}

    order = {"order_id": order_id, "status": "created"}

    IDEMPOTENCY_STORE[idempotency_key] = order

    return {"message": "Order created", "order": order}


if __name__ == "__main__":

    registry = {
        "echo": echo_tool,
        "flaky": flaky_tool,
        "permanent_failure": permanent_failure_tool,
        "always_transient": always_transient_tool,
        "create_order": create_order_tool
    }

    print("=== RETRY POLICY DEMO ===")

    print("\n1. Success without retry")

    result = execute_tool(registry, "echo", {"text": "hello"})

    print(result)

    print("\n2. Transient failure followed by retry")

    transient_counter["count"] = 0

    result = execute_tool(registry, "flaky",{"failures_before_success": 1,}, max_retries=2, backoff_s=0.05)

    print(result)

    print("\n3. Permanent failure - no retry")

    result = execute_tool(registry, "permanent_failure", {}, max_retries=2)

    print(result)

    print("\n4. Retry limit reached")

    result = execute_tool(registry, "always_transient", {}, max_retries=2, backoff_s=0.05)

    print(result)

    print("\n5. Idempotent write")

    first = execute_tool(registry, "create_order",{
            "order_id": "1001",
            "idempotency_key": "order-1001"})

    print(first)

    second = execute_tool(registry, "create_order", {
            "order_id": "1001",
            "idempotency_key": "order-1001"})

    print(second)