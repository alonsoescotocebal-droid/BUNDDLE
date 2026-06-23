"""Validation helpers for Phase 01B artifacts."""

from __future__ import annotations

from pathlib import Path


def build_phase01b_validation_summary(
    *,
    validation_rows: list[dict[str, object]],
    runtime_root: Path,
    required_outputs: tuple[str, ...],
    discovered_lags: list[int],
) -> list[dict[str, object]]:
    rows = list(validation_rows)
    rows.append(
        {
            "check_id": "strict_lag_discovery",
            "status": "PASS" if discovered_lags == [1, 2, 3, 4] else "FAIL",
            "severity": "error" if discovered_lags != [1, 2, 3, 4] else "info",
            "source_surface": "stat_root",
            "source_row_key": "lags",
            "details": f"discovered_lags={discovered_lags}",
        }
    )
    for relative_path in required_outputs:
        target = runtime_root / Path(relative_path.replace("/", "\\"))
        rows.append(
            {
                "check_id": "required_artifact_exists",
                "status": "PASS" if target.exists() else "FAIL",
                "severity": "error" if not target.exists() else "info",
                "source_surface": relative_path,
                "source_row_key": relative_path,
                "details": str(target),
            }
        )
    return rows
