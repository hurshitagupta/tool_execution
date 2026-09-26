## Task 1 — Dispatcher

### Objective
Implement a dispatcher that executes only registered tools, validates incoming requests, rejects unknown tools, and records an execution trace.

### Implementation
The dispatcher is implemented in:

```text
dispatcher.py
```

The tool registry contains the tools that are allowed to execute:

```python
registry = {
    "echo": echo_tool,
    "add": add_tool,
}
```

Before execution, the dispatcher:

1. Validates the tool name and arguments.
2. Checks whether the requested tool exists in the registry.
3. Executes only registered tools.
4. Captures execution failures.
5. Records execution duration and trace events.

Unknown tools are rejected with:

```text
tool_not_allowed
```

The execution trace records events such as:

```text
dispatch_started
tool_selected
execution_completed
dispatch_rejected
execution_failed
```

### Run Command

```powershell
python dispatcher.py
```

### Run Automated Tests

```powershell
pytest tests/test_dispatcher.py -v
```

### Evidence

```text
outputs/dispatcher.txt
outputs/test_dispatcher.txt
```

### Tests Covered
The automated tests verify:

- successful execution of a registered tool
- rejection of an unknown tool
- rejection of invalid request arguments
- handling of a tool execution failure

### Guardrails
- **Validation:** Tool name and arguments are validated before dispatch.
- **Execution boundary:** Only tools available in the registry can execute.
- **Traceability:** Dispatch and execution decisions are recorded in the returned trace.
- **Measurement:** Execution duration is returned as `duration_s`.
- **Secret hygiene:** No credentials or secrets are stored in the source code.
- **Retry/step limit:** Not applicable in this task because the dispatcher does not contain retry or execution loops.

---

## Task 2 — Timeout

### Objective
Implement a timeout mechanism so that tool execution does not wait indefinitely for a slow or hanging operation.

### Implementation
The timeout logic is implemented in:

```text
timeout.py
```

The implementation keeps the dispatcher behavior from Task 1 and adds a per-call timeout using `ThreadPoolExecutor`.

The tool is submitted using:

```python
future = executor.submit(registry[name], args)
```

The executor then waits only for the configured timeout:

```python
output = future.result(timeout=timeout_s)
```

If the tool finishes within the allowed time, the result returns:

```text
status = success
```

If the tool exceeds the allowed time, the result returns:

```text
status = timeout
error = execution_timeout
```

The timeout is also added to the execution trace as:

```text
execution_timeout
```

### Timeout Validation
The timeout value is validated before execution.

The request is rejected if:

- `timeout_s` is not a number
- `timeout_s` is zero
- `timeout_s` is negative

### Run Command

```powershell
python timeout.py
```

### Run Automated Tests

```powershell
pytest tests/test_timeout.py -v
```

### Save Program Output

```powershell
python timeout.py > outputs/timeout.txt
```

### Evidence

```text
outputs/timeout.txt
outputs/test_timeout.txt
```

### Tests Covered
The automated tests verify:

- a fast tool completes successfully before the timeout
- a slow tool returns a timeout result
- an invalid timeout value is rejected
- an unknown tool is rejected

### Guardrails
- **Timeout:** Each tool call has a configurable execution timeout.
- **Validation:** Tool name, arguments, and timeout value are validated before execution.
- **Execution boundary:** Only registered tools are executed.
- **Traceability:** Success, rejection, failure, and timeout events are recorded in the trace.
- **Measurement:** Execution duration is recorded as `duration_s`.
- **Secret hygiene:** No credentials or secrets are stored in source code.


