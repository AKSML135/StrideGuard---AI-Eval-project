# Failure gallery

Show failures, not only successful chats.

## Failure: false address-update confirmation

Case: `FALSE_SUCCESS_UPDATE_FAILURE`
System: `agent_v1`

Observed response:
"Your address was successfully updated."

Tool result:
```json
{"ok": false, "code": "UPDATE_FAILED"}
```

Final database state:
address = "5 Cedar Road"

Failure codes:
`FALSE_SUCCESS`, `FINAL_STATE_INCORRECT`

Root cause:
The response layer trusted the requested action rather than the tool result.

Fix:
Made a successful tool result a required workflow condition and added a
regression case with injected repository failure
(`OrderRepository(fail_updates=True)` in `src/strideguard/db.py`).

This proves that the eval suite led to an architectural improvement.

---

## Failure: (your entry here)

Case:
System:

Observed response:

Tool result:

Final database state:

Failure codes:

Root cause:

Fix:
