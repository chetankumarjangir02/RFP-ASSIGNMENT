"""CLI entrypoint (spec §9: runnable with one command).

Examples:
    python main.py index   --bid ./data/Bid1
    python main.py extract --bid ./data/Bid1 --out ./outputs/Bid1.json
    python main.py ask     --question "Is a bid bond required for Bid1?"
    python main.py serve
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _bid_id(folder: str) -> str:
    """Derive a bid id from a bid folder path (its final directory name)."""
    return Path(folder).name


def cmd_index(args: argparse.Namespace) -> None:
    from app.agents.ingestion_agent import ingest

    n = ingest(args.bid)
    print(f"Indexed {n} chunks from {args.bid}")


def cmd_extract(args: argparse.Namespace) -> None:
    from app.agents.graph import run_extraction

    bid_id = _bid_id(args.bid)
    out = args.out or f"./outputs/{bid_id}.json"
    record = run_extraction(bid_id, args.bid)

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(record.model_dump(), indent=2))
    print(f"Wrote {out}")


def cmd_ask(args: argparse.Namespace) -> None:
    from app.agents.graph import run_qa

    answer, evidence = run_qa(args.question, args.bid_id)
    print(answer)
    for e in evidence:
        meta = e.metadata
        print(f"  - {meta.get('file_name')} (page {meta.get('page_number')})")


def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn

    uvicorn.run(
        "app.api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RFP Intelligence Platform")
    sub = parser.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="Parse + index a bid folder")
    p_index.add_argument("--bid", required=True)
    p_index.set_defaults(func=cmd_index)

    p_extract = sub.add_parser("extract", help="Extract structured JSON for a bid folder")
    p_extract.add_argument("--bid", required=True)
    p_extract.add_argument("--out", default=None)
    p_extract.set_defaults(func=cmd_extract)

    p_ask = sub.add_parser("ask", help="Ask a question across indexed bids")
    p_ask.add_argument("--question", required=True)
    p_ask.add_argument("--bid-id", default=None)
    p_ask.set_defaults(func=cmd_ask)

    p_serve = sub.add_parser("serve", help="Run the FastAPI server")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
