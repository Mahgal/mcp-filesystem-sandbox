"""Minimal JSON-RPC-over-stdio MCP-style server for the filesystem sandbox.

Protocol: one JSON object per line on stdin, one JSON object per line on
stdout. Methods:

  list_resources  params: {}                       -> {"resources": [...]}
  read_resource   params: {"path": "<rel path>"}   -> {"path": ..., "content": ...}

Errors follow JSON-RPC 2.0: {"jsonrpc": "2.0", "id": ..., "error": {...}}.

Usage:
    python server.py --root <dir>
"""

from __future__ import annotations

import argparse
import json
import sys

from sandbox import SandboxError, list_resources, read_resource


def handle(request: dict, root: str) -> dict:
    req_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    def ok(result):
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def err(code, message):
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }

    try:
        if method == "list_resources":
            return ok({"resources": list_resources(root)})
        if method == "read_resource":
            path = params.get("path")
            if not isinstance(path, str) or not path:
                return err(-32602, "read_resource requires a string 'path' param")
            return ok({"path": path, "content": read_resource(root, path)})
        return err(-32601, f"method not found: {method!r}")
    except SandboxError as exc:
        return err(-32000, str(exc))
    except Exception as exc:  # defensive: never crash the stdio loop
        return err(-32603, f"internal error: {exc}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Sandboxed filesystem MCP server")
    parser.add_argument("--root", required=True, help="root directory to expose")
    args = parser.parse_args(argv)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            sys.stdout.write(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": f"parse error: {exc}"},
                    }
                )
                + "\n"
            )
            sys.stdout.flush()
            continue
        sys.stdout.write(json.dumps(handle(request, args.root)) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
