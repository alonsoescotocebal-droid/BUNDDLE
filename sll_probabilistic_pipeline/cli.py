"""CLI entrypoint."""

from __future__ import annotations

import argparse
import sys

from .config import SUPPORTED_PHASES
from .phase01a import run_phase01a
from .phase01b import run_phase01b
from .phase01b_join_repair import run_phase01b_join_repair
from .phase02 import run_phase02


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SLL probabilistic pipeline")
    parser.add_argument("--stat-root")
    parser.add_argument("--kin-root")
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--phase", default="phase01a")
    parser.add_argument("--repo-root")
    parser.add_argument("--phase01b-runtime")
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.phase not in SUPPORTED_PHASES:
        parser.error(f"Unsupported phase {args.phase!r}. Supported phases: {sorted(SUPPORTED_PHASES)}")
    if args.phase == "phase01a":
        if not args.stat_root or not args.kin_root:
            parser.error("--stat-root and --kin-root are required for phase01a")
        manifest = run_phase01a(
            stat_root=args.stat_root,
            kin_root=args.kin_root,
            out_root=args.out_root,
        )
        print("phase01a_complete")
        print(manifest["phase_status"])
        return 0
    if args.phase == "phase01b":
        if not args.stat_root or not args.kin_root:
            parser.error("--stat-root and --kin-root are required for phase01b")
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
    if args.phase == "phase01b_join_repair":
        if not args.repo_root:
            parser.error("--repo-root is required for phase01b_join_repair")
        if not args.phase01b_runtime:
            parser.error("--phase01b-runtime is required for phase01b_join_repair")
        manifest = run_phase01b_join_repair(
            repo_root=args.repo_root,
            phase01b_runtime=args.phase01b_runtime,
            out_root=args.out_root,
            strict=args.strict,
        )
        print("phase01b_join_repair_complete")
        print(manifest["phase02_plan_decision"])
        return 0
    if args.phase == "phase02":
        if args.stat_root or args.kin_root:
            parser.error("--stat-root and --kin-root are not accepted for phase02")
        if not args.repo_root:
            parser.error("--repo-root is required for phase02")
        if not args.phase01b_runtime:
            parser.error("--phase01b-runtime is required for phase02")
        manifest = run_phase02(
            repo_root=args.repo_root,
            phase01b_runtime=args.phase01b_runtime,
            out_root=args.out_root,
            strict=args.strict,
        )
        print("phase02_complete")
        print(manifest["phase_status"])
        print(manifest["phase02_completion_decision"])
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
