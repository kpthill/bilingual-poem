"""Candidate generation driver: multiple jittered beam-search runs, merged
and deduped, top-K by proxy score written as judge-ready JSON."""
import json, os, sys, argparse
import search

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--beam", type=int, default=4000)
    ap.add_argument("--runs", type=int, default=6)
    ap.add_argument("--jitter", type=float, default=1.2)
    ap.add_argument("--top", type=int, default=1200)
    ap.add_argument("--theme-id", default=None)
    ap.add_argument("--theme-fa", default=None)
    args = ap.parse_args()
    ti = json.load(open(args.theme_id)) if args.theme_id else None
    tf = json.load(open(args.theme_fa)) if args.theme_fa else None

    merged = {}
    funnel = {"runs": [], "total_raw": 0}
    for i in range(args.runs):
        targets = [(8, 9), (9, 10), (10, 11)][i % 3]
        lines, ide, fae, stats = search.run(
            seed_targets=targets, beam=args.beam,
            jitter=(0.0 if i == 0 else args.jitter), seed=i,
            theme_id=ti, theme_fa=tf, max_lines=3000, progress=False)
        funnel["runs"].append({"seed": i, "targets": targets,
                               "stats": stats, "lines": len(lines)})
        funnel["total_raw"] += stats["completed_raw"]
        for line in lines:
            r = search.render_line(line, ide, fae)
            key = (r["id"], r["fa_tr"])
            if key not in merged or merged[key]["score"] < r["score"]:
                merged[key] = r
        print(f"run {i} targets={targets}: {len(lines)} lines, "
              f"merged={len(merged)}", file=sys.stderr, flush=True)
    out = sorted(merged.values(), key=lambda r: -r["score"])[:args.top]
    funnel["merged_unique"] = len(merged)
    funnel["kept_for_judging"] = len(out)
    json.dump({"funnel": funnel, "candidates": out},
              open(args.out, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {len(out)} candidates -> {args.out}", file=sys.stderr)

if __name__ == "__main__":
    main()
