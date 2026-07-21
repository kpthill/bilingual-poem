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
    banned_id, banned_fa = {}, {}
    for i in range(args.runs):
        targets = [(8, 9), (9, 10), (10, 11)][i % 3]
        run_ti = dict(ti or {})
        run_tf = dict(tf or {})
        if i >= 2:      # later runs ban the emergent attractor words
            run_ti.update(banned_id)
            run_tf.update(banned_fa)
        lines, ide, fae, stats = search.run(
            seed_targets=targets, beam=args.beam,
            jitter=(0.0 if i == 0 else args.jitter), seed=i,
            theme_id=run_ti, theme_fa=run_tf, max_lines=3000,
            progress=False)
        funnel["runs"].append({"seed": i, "targets": targets,
                               "stats": stats, "lines": len(lines)})
        funnel["total_raw"] += stats["completed_raw"]
        from collections import Counter
        wc = Counter()
        for line in lines:
            r = search.render_line(line, ide, fae)
            key = (r["id"], r["fa_tr"])
            if key not in merged or merged[key]["score"] < r["score"]:
                merged[key] = r
            wc.update(r["id"].split())
        # ban this run's most-overused id words in later runs
        for w, n in wc.most_common(6):
            if n > len(lines) * 0.25:
                banned_id[w] = 1e-6
        print(f"run {i} targets={targets}: {len(lines)} lines, "
              f"merged={len(merged)} banned={sorted(banned_id)}",
              file=sys.stderr, flush=True)
    # diversified top-K: cap how often any word appears in the kept set
    from collections import Counter
    cap_id, cap_fa = Counter(), Counter()
    out = []
    for r in sorted(merged.values(), key=lambda r: -r["score"]):
        iw = r["id"].split()
        fw = r["fa_tr"].split()
        if any(cap_id[w] >= 25 for w in iw if len(w) > 3) or \
           any(cap_fa[w] >= 25 for w in fw if len(w) > 3):
            continue
        cap_id.update(w for w in iw if len(w) > 3)
        cap_fa.update(w for w in fw if len(w) > 3)
        out.append(r)
        if len(out) >= args.top:
            break
    funnel["merged_unique"] = len(merged)
    funnel["kept_for_judging"] = len(out)
    json.dump({"funnel": funnel, "candidates": out},
              open(args.out, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {len(out)} candidates -> {args.out}", file=sys.stderr)

if __name__ == "__main__":
    main()
