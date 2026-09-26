from result_envelope import execute_tool, echo_tool, divide_tool

def get_registry():
    return {"echo": echo_tool, "divide": divide_tool}

EXPECTED_FIELDS = {"status", "tool", "output", "error", "message", "duration_s", "trace"}

def test_success_result_envelope():
    registry = get_registry()

    result = execute_tool( registry, "echo", {"text": "hello"})

    assert result["status"] == "success"
    assert result["tool"] == "echo"
    assert result["output"] == "hello"
    assert result["error"] is None

    assert set(result.keys()) == EXPECTED_FIELDS

def test_failure_result_envelope():
    registry = get_registry()

    result = execute_tool( registry, "divide", {"a": 10, "b": 0})

    assert result["status"] == "error"
    assert result["tool"] == "divide"
    assert result["output"] is None
    assert result["error"] == "ZeroDivisionError"

    assert set(result.keys()) == EXPECTED_FIELDS

def test_rejected_result_envelope():
    registry = get_registry()

    result = execute_tool(registry, "unknown_tool", {})

    assert result["status"] == "rejected"
    assert result["output"] is None
    assert result["error"] == "tool_not_allowed"
    assert set(result.keys()) == EXPECTED_FIELDS

def test_invalid_arguments_use_same_envelope():
    registry = get_registry()

    result = execute_tool( registry, "echo", "invalid")

    assert result["status"] == "rejected"
    assert result["error"] == "invalid_request"

    assert set(result.keys()) == EXPECTED_FIELDS