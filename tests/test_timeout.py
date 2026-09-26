from timeout import execute_tool, fast_tool, slow_tool


def get_registry():
    return { "fast": fast_tool, "slow": slow_tool}


def test_tool_completes_before_timeout():
    registry = get_registry()

    result = execute_tool( registry, "fast", {"text": "hello"}, timeout_s=1.0)

    assert result["status"] == "success"
    assert result["output"] == "Processed: hello"

    events = [item["event"] for item in result["trace"]]

    assert "execution_completed" in events


def test_tool_timeout():
    registry = get_registry()

    result = execute_tool(registry, "slow", {"delay": 0.2}, timeout_s=0.05)

    assert result["status"] == "timeout"
    assert result["error"] == "execution_timeout"
    assert result["timeout_s"] == 0.05

    events = [item["event"] for item in result["trace"]]

    assert "execution_timeout" in events


def test_invalid_timeout_is_rejected():
    registry = get_registry()

    result = execute_tool( registry, "fast", {"text": "hello"}, timeout_s=0)

    assert result["status"] == "rejected"
    assert result["error"] == "invalid_request"


def test_unknown_tool_is_rejected():
    registry = get_registry()

    result = execute_tool(registry, "unknown_tool", {}, timeout_s=1.0)

    assert result["status"] == "rejected"
    assert result["error"] == "tool_not_allowed"