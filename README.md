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
