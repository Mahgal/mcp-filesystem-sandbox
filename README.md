# mcp-filesystem-sandbox

Give an AI agent read-only access to one folder — and provably nothing outside it.

## Quick start

```bash
# stdlib only, Python 3.10+
python server.py --root demo
```

Then send one JSON object per line on stdin. Three requests:

```json
{"jsonrpc":"2.0","id":1,"method":"list_resources","params":{}}
{"jsonrpc":"2.0","id":2,"method":"read_resource","params":{"path":"notes.md"}}
{"jsonrpc":"2.0","id":3,"method":"read_resource","params":{"path":"../secret.txt"}}
```

## Example output

Real output from the run in `SMOKE.md` (2026-11-10):

```json
{"jsonrpc": "2.0", "id": 1, "result": {"resources": ["code/hello.py", "data/todo.txt", "notes.md"]}}
{"jsonrpc": "2.0", "id": 2, "result": {"path": "notes.md", "content": "# Demo project\n\nA tiny sample tree served by the sandbox.\n\n- `notes.md` — what this demo is\n- `code/hello.py` — a two-line Python script\n- `data/todo.txt` — a small checklist\n"}}
{"jsonrpc": "2.0", "id": 3, "error": {"code": -32000, "message": "path escapes the sandbox root: '../secret.txt'"}}
```

The third request is the point: `demo/../secret.txt` exists on disk, but the
server refuses it — `..` traversal never leaves the root.

## Tests

```bash
python -m unittest discover -s tests -v
# 9 tests, all passing
```

## Security notes

- Every path is resolved against the root **after** resolving symlinks, so a
  symlink pointing outside the root is rejected just like `..` traversal.
- Absolute paths are rejected outright; everything is relative to the root.
- Hidden files and directories (`.git`, `.env`, …) are never listed.
- Reads are capped at 1 MB by default (`DEFAULT_MAX_BYTES` in `sandbox.py`).
- The server is read-only by design: there is no write, delete, or exec
  method at all, and it makes no network calls.
- This is a minimal demo sandbox, not a hardened security boundary — do not
  expose it to untrusted input without an additional layer.

## License

MIT — see `LICENSE`.
