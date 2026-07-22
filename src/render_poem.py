"""Render final_poem.json (+ audits, coherence) into poem.md."""
import json, os, sys

BUILD = os.path.join(os.path.dirname(__file__), "..", "data", "build")

def main(out_path):
    fp = json.load(open(os.path.join(BUILD, "final_poem.json")))
    try:
        audit_id = {a["line"]: a for a in
                    json.load(open(os.path.join(BUILD, "audit_id.json")))}
        audit_fa = {a["line"]: a for a in
                    json.load(open(os.path.join(BUILD, "audit_fa.json")))}
    except FileNotFoundError:
        audit_id, audit_fa = {}, {}
    lines = fp["lines"]
    total_cost = sum(L["accent_cost"] for L in lines)
    total_syll = sum(L["sylls"] for L in lines)

    md = []
    md.append(f"# {fp.get('title_id','')} / {fp.get('title_fa','')} "
              f"({fp.get('title_fa_translit','')})\n")
    md.append("*A phonetically dual-language poem: one phoneme stream, "
              "two readings.*\n")
    md.append("Read aloud in the compromise accent, every line below is "
              "simultaneously an Indonesian line (left gloss) and a Persian "
              "line (right gloss), with different word boundaries.\n")

    md.append("## The poem\n")
    for i, L in enumerate(lines, 1):
        md.append(f"### {i}.\n")
        md.append(f"**IPA (shared stream):** `{L['ipa_compromise']}`\n")
        md.append(f"| | text | literal English |")
        md.append(f"|---|---|---|")
        md.append(f"| **Indonesian** | *{L['indonesian']}* | "
                  f"{L['gloss_id']} |")
        md.append(f"| **Persian** | {L['persian_script']} — "
                  f"*{L['persian_translit']}* | {L['gloss_fa']} |")
        md.append("")

    md.append("## Per-line accent-cost annotations\n")
    md.append("Cost table: see `src/phonespace.py`. "
              f"Poem totals: **{total_cost:.1f} cost / {total_syll} "
              f"syllables = {total_cost/total_syll:.2f} per syllable**.\n")
    md.append("| # | syll | cost | compromises |")
    md.append("|---|---|---|---|")
    for i, L in enumerate(lines, 1):
        notes = "; ".join(L["notes"]) if L["notes"] else "none — identical streams"
        md.append(f"| {i} | {L['sylls']} | {L['accent_cost']} | {notes} |")
    md.append("")

    if audit_id:
        md.append("## Blind recoverability audit\n")
        md.append("Independent auditors were shown ONLY the IPA stream "
                  "(no intended readings) and asked what they hear.\n")
        md.append("| # | Indonesian ear heard (score/5) | Persian ear heard (score/5) |")
        md.append("|---|---|---|")
        for i, L in enumerate(lines, 1):
            a, b = audit_id.get(i, {}), audit_fa.get(i, {})
            md.append(f"| {i} | {a.get('heard','—')} "
                      f"({a.get('recoverability','—')}) | "
                      f"{b.get('heard','—')} ({b.get('recoverability','—')}) |")
        md.append("")

    open(out_path, "w").write("\n".join(md))
    print("wrote", out_path)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../poem.md")
