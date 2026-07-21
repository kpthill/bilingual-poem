"""LLM judging: batch preparation, result merging, line scoring.

Two ways to obtain scores:
  1. `prepare` writes self-contained batch files; any LLM (or a Claude
     subagent) reads a batch file and writes a JSON score file next to it.
  2. `api` calls the Anthropic API directly (needs ANTHROPIC_API_KEY).

Scoring (from the task spec):
  reject if G_id < 3 or G_fa < 3
  A = 1 / (1 + accent_cost / syllables)
  line_score = min(M_id, M_fa) + 0.7*avg(M_id, M_fa)
               + 0.5*(G_id + G_fa) + 2.0*A
"""
import json, os, sys, argparse, glob

JUDGE_INSTRUCTIONS = """You are judging candidate lines for a bilingual \
phonetic poem. Each candidate is ONE phoneme stream that should read as a \
line of poetry in BOTH Indonesian and Persian (with different word \
boundaries). For each candidate below, judge the two readings INDEPENDENTLY:

- M (meaningfulness, 0-5): does this reading convey semantic content a
  native reader would recognize as an intentional line of poetry (imagery,
  statement, address)? Gnomic/surreal is fine ("Two lands bathe" = 4).
  Word salad = 0-1. A grammatical but empty function-word string = 1-2.
- G (grammaticality, 0-5): is it syntactically well-formed in the POETIC
  register? Dropped copula (Indonesian), verb-final flexibility and
  right-dislocation (Persian verse) are fine at most -1. Agreement errors,
  impossible word orders, bare determiner+clitic nonsense = 0-2.

Also:
- gloss each reading into literal English,
- flags: "fp" if a segmentation uses a technically-existing but unparseable
  word (rare archaism, wrong register, or a Wiktionary ghost entry);
  "loan" if the two readings rely on a shared Arabic/Persian loanword with
  essentially the same meaning in both languages (e.g. dunia/donyâ);
  "script" if the Persian orthography given is wrong for the intended words.

The Persian is given in Latin transliteration (â = long a, ' = glottal stop,
kh = خ, q = ق/غ) plus tentative script. Trust the transliteration; the
script may contain small errors (note "script" flag).
Persian morphology tags appear as -e (ezâfe), -i (indefinite), -am/-and
(copula/verb endings): verify an ezâfe actually links linkable things.

Be strict. Most candidates are garbage; scores of 0-2 are the norm.
Return ONLY a JSON array, one object per candidate:
{"i": <index>, "M_id": n, "G_id": n, "M_fa": n, "G_fa": n,
 "gloss_id": "...", "gloss_fa": "...", "flags": [], "note": "<=15 words"}
"""

def prepare(candidates_file, outdir, batch_size=35, limit=None):
    data = json.load(open(candidates_file))
    cands = data["candidates"] if "candidates" in data else data
    if limit:
        cands = cands[:limit]
    os.makedirs(outdir, exist_ok=True)
    nb = 0
    for b in range(0, len(cands), batch_size):
        batch = cands[b:b + batch_size]
        items = []
        for j, c in enumerate(batch):
            items.append({
                "i": b + j,
                "indonesian": c["id"],
                "persian_translit": c["fa_tr"],
                "persian_script": c["fa"],
                "persian_tags": c.get("fa_tags"),
                "ipa": c.get("ipa_id"),
            })
        path = os.path.join(outdir, f"batch_{b//batch_size:03d}.json")
        json.dump({"instructions": JUDGE_INSTRUCTIONS, "items": items},
                  open(path, "w"), ensure_ascii=False, indent=1)
        nb += 1
    print(f"wrote {nb} batches ({len(cands)} lines) -> {outdir}")

def line_score(c, s):
    if s["G_id"] < 3 or s["G_fa"] < 3:
        return None
    A = 1.0 / (1.0 + c["cost"] / max(c["sylls"], 1))
    m = (s["M_id"] + s["M_fa"]) / 2.0
    sc = min(s["M_id"], s["M_fa"]) + 0.7 * m \
        + 0.5 * (s["G_id"] + s["G_fa"]) + 2.0 * A
    if "fp" in s.get("flags", []):
        sc -= 2.0
    return sc

def merge(candidates_file, scores_glob, out):
    data = json.load(open(candidates_file))
    cands = data["candidates"] if "candidates" in data else data
    scores = {}
    bad = 0
    for path in sorted(glob.glob(scores_glob)):
        try:
            arr = json.load(open(path))
        except json.JSONDecodeError:
            print("unparseable:", path, file=sys.stderr)
            continue
        for s in arr:
            try:
                i = int(s["i"])
                for k in ("M_id", "G_id", "M_fa", "G_fa"):
                    s[k] = max(0, min(5, int(s[k])))
                scores[i] = s
            except (KeyError, ValueError, TypeError):
                bad += 1
    judged, rejected = [], 0
    for i, c in enumerate(cands):
        s = scores.get(i)
        if s is None:
            continue
        ls = line_score(c, s)
        rec = dict(c)
        rec.update({"judge": s, "line_score": ls})
        if ls is None:
            rejected += 1
        judged.append(rec)
    judged.sort(key=lambda r: -(r["line_score"] or -99))
    json.dump(judged, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"merged {len(scores)} scores ({bad} malformed), "
          f"{rejected} rejected by G-floor -> {out}")

def api_judge(batch_dir, model="claude-sonnet-5"):
    import urllib.request
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ANTHROPIC_API_KEY not set; use subagent/manual judging "
                 "of the batch files instead.")
    for path in sorted(glob.glob(os.path.join(batch_dir, "batch_*.json"))):
        out_path = path.replace("batch_", "scores_")
        if os.path.exists(out_path):
            continue
        batch = json.load(open(path))
        body = json.dumps({
            "model": model, "max_tokens": 8000,
            "messages": [{"role": "user", "content":
                          batch["instructions"] + "\n\n" +
                          json.dumps(batch["items"], ensure_ascii=False)}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=body,
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            txt = json.load(resp)["content"][0]["text"]
        txt = txt[txt.index("["):txt.rindex("]") + 1]
        open(out_path, "w").write(txt)
        print("judged", path)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("candidates"); p.add_argument("outdir")
    p.add_argument("--batch-size", type=int, default=35)
    p.add_argument("--limit", type=int, default=None)
    m = sub.add_parser("merge")
    m.add_argument("candidates"); m.add_argument("scores_glob")
    m.add_argument("out")
    a = sub.add_parser("api")
    a.add_argument("batch_dir"); a.add_argument("--model",
                                                default="claude-sonnet-5")
    args = ap.parse_args()
    if args.cmd == "prepare":
        prepare(args.candidates, args.outdir, args.batch_size, args.limit)
    elif args.cmd == "merge":
        merge(args.candidates, args.scores_glob, args.out)
    else:
        api_judge(args.batch_dir, args.model)
