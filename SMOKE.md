# SMOKE.md — real runs, 2026-11-10

Working directory for all commands:
`~/workspace/github-factory/2026-11-10/mcp-filesystem-sandbox/`

## 1. Unit tests

Command:

```bash
python3 -m unittest discover -s tests -v
```

Exit code: **0**

Result: `Ran 9 tests in 0.081s — OK`
(9/9 pass: traversal blocked, symlink escape blocked, symlink inside root
allowed, hidden files filtered, normal read works, root itself listed,
absolute path rejected, missing file, size cap.)

## 2. Live demo (JSON-RPC over stdio)

Command:

```bash
printf '%s\n%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"list_resources","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"read_resource","params":{"path":"notes.md"}}' \
  '{"jsonrpc":"2.0","id":3,"method":"read_resource","params":{"path":"../secret.txt"}}' \
  | python3 server.py --root demo
```

Exit code: **0**

Real output:

```json
{"jsonrpc": "2.0", "id": 1, "result": {"resources": ["code/hello.py", "data/todo.txt", "notes.md"]}}
{"jsonrpc": "2.0", "id": 2, "result": {"path": "notes.md", "content": "# Demo project\n\nA tiny sample tree served by the sandbox.\n\n- `notes.md` — what this demo is\n- `code/hello.py` — a two-line Python script\n- `data/todo.txt` — a small checklist\n"}}
{"jsonrpc": "2.0", "id": 3, "error": {"code": -32000, "message": "path escapes the sandbox root: '../secret.txt'"}}
```

- `list_resources` → 3 files, exit 0.
- `read_resource notes.md` → content returned, exit 0.
- `read_resource ../secret.txt` → blocked with error `-32000`
  ("path escapes the sandbox root"), exit 0. The file exists on disk at
  `demo/../secret.txt` but is unreachable through the server.

## Failures

None. No test failed, no demo step failed.
