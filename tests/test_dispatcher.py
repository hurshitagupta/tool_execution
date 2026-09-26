from dispatcher import execute_tool, echo_tool, add_tool


def get_registry():
    return {"echo": echo_tool, "add": add_tool}


def test_dispatch_success():
    registry = get_registry()

    result = execute_tool(registry, "echo", {"text": "hello"})

    assert result["status"] == "success"
    assert result["output"] == "hello"
    assert result["duration_s"] >= 0

    events = [item["event"] for item in result["trace"]]

    assert "dispatch_started" in events
    assert "tool_selected" in events
    assert "execution_completed" in events


def test_unknown_tool_is_rejected():
    registry = get_registry()

    result = execute_tool( registry, "unknown_tool", {})

    assert result["status"] == "rejected"
    assert result["error"] == "tool_not_allowed"

    events = [item["event"] for item in result["trace"]]

    assert "dispatch_rejected" in events


def test_invalid_arguments_are_rejected():
    registry = get_registry()

    result = execute_tool(registry, "echo", "invalid arguments")

    assert result["status"] == "rejected"
    assert result["error"] == "invalid_request"


def test_tool_failure_is_captured():
    registry = get_registry()

    result = execute_tool(registry, "add",{ "a": 10, "b": "invalid"})

    assert result["status"] == "error"
    assert result["error"] == "ValueError"