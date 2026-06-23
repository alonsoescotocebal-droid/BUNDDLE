"""CLI entrypoint."""

from __future__ import annotations

import argparse
import sys

from .config import SUPPORTED_PHASES
from .phase01a import run_phase01a
from .phase01b import run_phase01b


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SLL probabilistic pipeline")
    parser.add_argument("--stat-root", required=True)
    parser.add_argument("--kin-root", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--phase", default="phase01a")
    parser.add_argument("--repo-root")
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.phase not in SUPPORTED_PHASES:
        parser.error(f"Unsupported phase {args.phase!r}. Supported phases: {sorted(SUPPORTED_PHASES)}")
    if args.phase == "phase01a":
        manifest = run_phase01a(
            stat_root=args.stat_root,
            kin_root=args.kin_root,
            out_root=args.out_root,
        )
        print("phase01a_complete")
        print(manifest["phase_status"])
        return 0
    if args.phase == "phase01b":
        if not args.repo_root:
            parser.error("--repo-root is required for phase01b")
        manifest = run_phase01b(
            repo_root=args.repo_root,
            stat_root=args.stat_root,
            kin_root=args.kin_root,
            out_root=args.out_root,
            strict=args.strict,
        )
        print("phase01b_complete")
        print(manifest["phase_status"])
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
