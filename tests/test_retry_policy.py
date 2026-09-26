from retry_policy import execute_tool, echo_tool, flaky_tool, permanent_failure_tool, always_transient_tool, create_order_tool, transient_counter, IDEMPOTENCY_STORE


def get_registry():
    return {
        "echo": echo_tool,
        "flaky": flaky_tool,
        "permanent_failure": permanent_failure_tool,
        "always_transient": always_transient_tool,
        "create_order": create_order_tool
    }


def test_success_without_retry():
    registry = get_registry()

    result = execute_tool(registry, "echo", {"text": "hello"})

    assert result["status"] == "success"
    assert result["output"] == "hello"
    assert result["attempts"] == 1
    assert result["retries"] == 0


def test_transient_failure_is_retried():
    registry = get_registry()

    transient_counter["count"] = 0

    result = execute_tool(registry, "flaky", {"failures_before_success": 1}, max_retries=2, backoff_s=0)

    assert result["status"] == "success"
    assert result["attempts"] == 2
    assert result["retries"] == 1

    events = [event["event"] for event in result["trace"]]

    assert "transient_failure" in events
    assert "retry_scheduled" in events
    assert "execution_completed" in events


def test_permanent_failure_is_not_retried():
    registry = get_registry()

    result = execute_tool(registry, "permanent_failure", {}, max_retries=2)

    assert result["status"] == "error"
    assert result["attempts"] == 1
    assert result["retries"] == 0
    assert result["error"] == "PermanentToolError"


def test_retry_limit_is_enforced():
    registry = get_registry()

    result = execute_tool(registry, "always_transient",{}, max_retries=2, backoff_s=0)

    assert result["status"] == "error"
    assert result["error"] == "retry_limit_reached"
    assert result["attempts"] == 3
    assert result["retries"] == 2


def test_retry_limit_validation():
    registry = get_registry()

    result = execute_tool(registry, "echo", {"text": "hello"}, max_retries=10)

    assert result["status"] == "rejected"
    assert result["error"] == "invalid_request"


def test_idempotency_prevents_duplicate_write():
    registry = get_registry()

    IDEMPOTENCY_STORE.clear()

    args = {"order_id": "1001", "idempotency_key": "order-1001"}

    first = execute_tool(registry, "create_order", args)

    second = execute_tool(registry, "create_order", args)

    assert first["status"] == "success"
    assert second["status"] == "success"

    assert first["output"]["order"] == second["output"]["order"]

    assert len(IDEMPOTENCY_STORE) == 1