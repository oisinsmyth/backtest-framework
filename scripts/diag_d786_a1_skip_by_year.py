"""Scratch, in-sample (already read by D788, formerly D786): family A's skip share by year per index book, dollar form, to see
whether the dollar bar still skips anything at late-sample prices (the vault's NQ is higher still)."""
import sys
from pathlib import Path

WT = Path("C:/Users/O/Desktop/Projects/Backtest Framework/.claude/worktrees/after-d674")
sys.path.insert(0, str(WT / "scripts"))
sys.path.insert(0, str(WT / "src"))
import diag_d786_abstention_oracle as A  # noqa: E402


def main():
    books, cost = A.load_books()
    closes = {r: A.daily_closes(r) for r in ("NQ", "RTY")}
    stf = {r: A.state_frame(c, A.MULT[r]) for r, c in closes.items()}
    for b in ("D737", "NQ_F2", "C1", "D776", "L4"):
        y = A.book_states(books[b], b, cost[b], stf[A.ROOT[b]], stf["NQ"])
        z = y[y["A_proj_ge_2c"].notna()]
        sk = (~z["A_proj_ge_2c"].astype(bool)).groupby(z["year"]).mean().round(2)
        print(b, "skip share by year:", sk.to_dict())


if __name__ == "__main__":
    main()
