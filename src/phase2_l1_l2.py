from __future__ import annotations
import json, math
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import numpy as np

from src.backtest_runner import run_backtest_nautilus_trackA, BacktestParams

ART = Path("artifacts"); ART.mkdir(exist_ok=True, parents=True)
REP = Path("reports");   REP.mkdir(exist_ok=True, parents=True)

GRID = {
    "ma_short": [10, 15, 20],
    "ma_long":  [30, 40, 50],
    "rsi_period": [10, 14],
    "rsi_low":  [20, 30],
    "rsi_high": [70, 80],
}

def write_indicator_cfg(ms, ml, rp, rl, rh):
    cfg = dict(ma_short=ms, ma_long=ml, rsi_period=rp, rsi_low=rl, rsi_high=rh)
    ART.joinpath("indicator_config.json").write_text(json.dumps(cfg))

def sweep(mode: str, seed=42) -> pd.DataFrame:
    rows = []
    for ms in GRID["ma_short"]:
        for ml in GRID["ma_long"]:
            if ms >= ml: continue
            for rp in GRID["rsi_period"]:
                for rl in GRID["rsi_low"]:
                    for rh in GRID["rsi_high"]:
                        if rl >= rh: continue
                        write_indicator_cfg(ms, ml, rp, rl, rh)
                        params = BacktestParams(
                            mode=mode, seed=seed,
                            prob_slippage=0.5,  # L1
                            spread_ticks=1,     # L2*
                            depth_profile=(2,3,5,8,13),  # L2*
                            fees_bps=1.0
                        )
                        res = run_backtest_nautilus_trackA(params=params)
                        res["equity_curve"].to_csv(ART / f"equity_{mode}_{ms}_{ml}_{rp}_{rl}_{rh}.csv", index=False)
                        rows.append({
                            "mode": mode, "ma_short": ms, "ma_long": ml, "rsi_period": rp,
                            "rsi_low": rl, "rsi_high": rh,
                            "final_equity": res["final_equity"],
                            "max_dd": res["max_drawdown"],
                            "sharpe": res["daily_sharpe"],
                        })
    df = pd.DataFrame(rows).sort_values(["sharpe","final_equity"], ascending=[False, False])
    out_csv = ART / f"phase2_{mode}_results.csv"
    df.to_csv(out_csv, index=False)
    return df

def main():
    df_l1 = sweep("L1", seed=42)
    df_l2 = sweep("L2", seed=42)
    best_l1 = df_l1.iloc[0].to_dict() if len(df_l1) else {}
    best_l2 = df_l2.iloc[0].to_dict() if len(df_l2) else {}
    ART.joinpath("best_L1.json").write_text(json.dumps(best_l1, indent=2))
    ART.joinpath("best_L2.json").write_text(json.dumps(best_l2, indent=2))

    rep = [
        "# Phase 2 — L1 vs L2* Report",
        "## Best L1",
        "```json", json.dumps(best_l1, indent=2), "```",
        "## Best L2* (synthetic depth)",
        "```json", json.dumps(best_l2, indent=2), "```",
        "## Notes",
        "- L1 = bar/top-of-book with probabilistic 1-tick slippage.",
        "- L2* = synthetic depth ladder built from close price, spread=1 tick, 5 levels.",
        "- Deterministic seed=42; indicators from prior bars only (no look-ahead).",
        f"- Full tables: artifacts/phase2_L1_results.csv & artifacts/phase2_L2_results.csv",
    ]
    REP.joinpath("PHASE2_L1_L2_REPORT.md").write_text("\n".join(rep))
    print("Wrote reports/PHASE2_L1_L2_REPORT.md")

if __name__ == "__main__":
    main()
