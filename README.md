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

---

## Task 3 — Retry Policy

### Objective
Implement a retry policy that retries only transient failures, applies a retry limit, uses capped backoff, and avoids duplicate write side effects using idempotency keys.

### Implementation
The retry logic is implemented in:

```text
retry_policy.py
```

The implementation classifies failures into:

```text
TransientToolError
PermanentToolError
```

Only transient failures are retried.

Permanent or unclassified failures return immediately without another attempt.

### Retry Limit
The number of attempts is controlled using:

```python
total_attempts = max_retries + 1
```

for a maximum of three execution attempts.

The retry value is also validated so that it cannot exceed the configured hard limit of `3`.

### Retry Backoff
A delay is applied between retries using:

```python
delay = min(backoff_s * attempt, 0.5)
```

This creates a small increasing delay while ensuring the wait never exceeds `0.5` seconds.

### Failure Classification
Transient failures are handled using:

```python
except TransientToolError:
```

and may be retried.

Permanent failures are handled using:

```python
except PermanentToolError:
```

and are not retried.

### Idempotency
The `create_order_tool` demonstrates protection against duplicate write operations.

Each write includes an:

```text
idempotency_key
```

Before creating the order, the tool checks:

```python
if idempotency_key in IDEMPOTENCY_STORE:
```

If the same operation was already completed, the existing result is returned instead of creating another order.

This demonstrates that exactly-once execution is not automatic and that write retries require additional protection.

### Run Command

```powershell
python retry_policy.py
```

### Run Automated Tests

```powershell
pytest tests/test_retry_policy.py -v
```

### Save Program Output

```powershell
python retry_policy.py > outputs/retry_policy.txt
```

### Save Test Output

```powershell
pytest tests/test_retry_policy.py -v > outputs/test_retry_policy.txt
```

### Evidence

```text
outputs/retry_policy.txt
outputs/test_retry_policy.txt
```

### Tests Covered
The automated tests verify:

- successful execution without retry
- transient failure followed by successful retry
- permanent failure without retry
- retry limit enforcement
- invalid retry configuration rejection
- duplicate write prevention using an idempotency key

### Guardrails
- **Step/retry limit:** Retry attempts are limited using `max_retries`, with a hard maximum of 3 retries.
- **Retry policy:** Only classified transient failures are retried.
- **Backoff:** Retries use capped backoff.
- **Validation:** Tool name, arguments, retry count, and backoff values are validated.
- **Execution boundary:** Only registered tools can execute.
- **Traceability:** Every attempt, failure, retry, and final result is recorded in the trace.
- **Measurement:** Execution duration, attempt count, and retry count are returned.
- **Side-effect protection:** Idempotency keys prevent duplicate write operations.
- **Secret hygiene:** No credentials or secrets are stored in source code.

---

## Task 4 — Result Envelope

### Objective
Implement a consistent result envelope so that every tool execution returns the same structured response format for success, failure, or rejection.

### Implementation
The result envelope is implemented in:

```text
result_envelope.py
```

A typed result structure is defined using:

```python
class ResultEnvelope(TypedDict):
```

Every result contains the following fields:

```text
status
tool
output
error
message
duration_s
trace
```

The `make_result()` function is used to construct the result consistently:

```python
def make_result(...)
```

This avoids returning different response structures for different execution outcomes.

### Success Result
A successful execution returns:

```text
status = success
output = tool result
error = None
```

The result also includes the tool name, execution duration, message, and trace.

### Failure Result
If the tool raises an exception, the same envelope is returned with:

```text
status = error
output = None
error = exception type
```

For example, division by zero returns:

```text
error = ZeroDivisionError
```

### Rejected Result
Unknown tools or invalid requests also use the same result structure.

For an unknown tool:

```text
status = rejected
error = tool_not_allowed
```

### Run Command

```powershell
python result_envelope.py
```

### Run Automated Tests

```powershell
pytest tests/test_result_envelope.py -v
```

### Evidence

```text
outputs/result_envelope.txt
outputs/test_result_envelope.txt
```

---

## Task 5 — Execution Metrics

### Objective
Implement execution metrics so that tool behavior can be measured using concrete counts, success and error rates, and execution duration.

### Implementation
The metrics implementation is in:

```text
execution_metrics.py
```

The `ExecutionMetrics` class tracks:

```text
total_executions
success_count
error_count
rejected_count
total_duration_s
```

Every execution result is recorded using:

```python
metrics.record(status, duration_s)
```

The final measurements are returned using:

```python
metrics.summary()
```

### Metrics Produced
The summary contains:

```text
total_executions
success_count
error_count
rejected_count
success_rate_percent
error_rate_percent
average_duration_s
```

This provides measurable evidence of how the executor behaves across successful, failed, and rejected tool calls.

### Demonstrated Execution Cases
The implementation demonstrates:

- successful `echo` execution
- successful `divide` execution
- failed division by zero
- rejected unknown tool

These calls produce a final metrics summary showing total executions and outcome rates.

### Run Command

```powershell
python execution_metrics.py
```

### Run Automated Tests

```powershell
pytest tests/test_execution_metrics.py -v
```

### Tests Covered
The automated tests verify:

- successful executions update success metrics
- failed executions update error metrics
- rejected executions update rejection metrics
- multiple executions produce the correct combined counts
- success rate and error rate are calculated correctly
- average execution duration is recorded