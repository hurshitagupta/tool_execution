from execution_metrics import ExecutionMetrics, execute_tool, echo_tool, divide_tool

def get_registry():
    return {"echo": echo_tool, "divide": divide_tool}

def test_success_metrics():
    registry = get_registry()
    metrics = ExecutionMetrics()

    result = execute_tool(registry, "echo", {"text": "hello"}, metrics)

    summary = metrics.summary()

    assert result["status"] == "success"
    assert summary["total_executions"] == 1
    assert summary["success_count"] == 1
    assert summary["error_count"] == 0
    assert summary["rejected_count"] == 0
    assert summary["success_rate_percent"] == 100.0


def test_error_metrics():
    registry = get_registry()
    metrics = ExecutionMetrics()

    result = execute_tool(registry, "divide", {"a": 10, "b": 0}, metrics)

    summary = metrics.summary()

    assert result["status"] == "error"
    assert summary["total_executions"] == 1
    assert summary["success_count"] == 0
    assert summary["error_count"] == 1
    assert summary["error_rate_percent"] == 100.0


def test_rejected_metrics():
    registry = get_registry()
    metrics = ExecutionMetrics()

    result = execute_tool(registry, "unknown_tool", {}, metrics)

    summary = metrics.summary()

    assert result["status"] == "rejected"
    assert summary["total_executions"] == 1
    assert summary["rejected_count"] == 1


def test_combined_metrics():
    registry = get_registry()
    metrics = ExecutionMetrics()

    execute_tool(registry, "echo", {"text": "hello"}, metrics)

    execute_tool(registry,"divide",{"a": 10,"b": 2}, metrics)

    execute_tool(registry, "divide", {"a": 10,"b": 0}, metrics)

    execute_tool(registry, "unknown_tool", {}, metrics)

    summary = metrics.summary()

    assert summary["total_executions"] == 4
    assert summary["success_count"] == 2
    assert summary["error_count"] == 1
    assert summary["rejected_count"] == 1

    assert summary["success_rate_percent"] == 50.0
    assert summary["error_rate_percent"] == 25.0

    assert summary["average_duration_s"] >= 0