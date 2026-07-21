"""Poem assembly: pick N lines from the judged pool.

Greedy selection over line_score with diversity constraints:
- no Indonesian or Persian content word used in more than 2 lines
- at most `max_loans` lines flagged "loan" (shared-loanword party tricks)
- optional theme keywords to prefer
Emits several alternative assemblies (different tradeoffs) for the
poem-level coherence judge to rank.
"""
import json, argparse
from collections import Counter

def select(judged, n=20, max_loans=2, word_cap=2, min_score=None,
           prefer=None):
    pool = [r for r in judged if r.get("line_score")]
    if min_score:
        pool = [r for r in pool if r["line_score"] >= min_score]
    pool.sort(key=lambda r: -(r["line_score"]
                              + (1.0 if prefer and any(w in r["id"].split()
                                 for w in prefer) else 0.0)))
    chosen, cap_id, cap_fa, loans = [], Counter(), Counter(), 0
    for r in pool:
        iw = [w for w in r["id"].split() if len(w) > 3]
        fw = [w for w in r["fa_tr"].split() if len(w) > 3]
        if any(cap_id[w] >= word_cap for w in iw):
            continue
        if any(cap_fa[w] >= word_cap for w in fw):
            continue
        is_loan = "loan" in r["judge"].get("flags", [])
        if is_loan and loans >= max_loans:
            continue
        chosen.append(r)
        cap_id.update(iw)
        cap_fa.update(fw)
        loans += is_loan
        if len(chosen) >= n:
            break
    return chosen

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("judged")
    ap.add_argument("out")
    ap.add_argument("-n", type=int, default=20)
    args = ap.parse_args()
    judged = json.load(open(args.judged))
    variants = {
        "top": select(judged, n=args.n),
        "strict": select(judged, n=args.n, min_score=8.0),
        "diverse": select(judged, n=args.n, word_cap=1),
    }
    json.dump({k: v for k, v in variants.items()},
              open(args.out, "w"), ensure_ascii=False, indent=1)
    for k, v in variants.items():
        print(f"--- {k}: {len(v)} lines")
        for r in v[:25]:
            print(f"  [{r['line_score']:.1f}] {r['id']}  ||  {r['fa_tr']}")

if __name__ == "__main__":
    main()
