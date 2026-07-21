"""Lattice-intersection beam search.

Walks Indonesian and Persian pronunciation tries in lockstep, consuming one
shared segment at a time (a pair of phones with finite match cost). Special
moves: fa-side ʔ/h epsilon deletion (intervocalic), id-side h deletion, and
the V+h / h+V metathesis. A line is complete when both sides sit at a word
boundary and the syllable count is in range.
"""
import math, heapq, argparse, json, os, sys
from collections import defaultdict
from phonespace import match_cost, is_vowel, EPSILON_COST, FA_DELETABLE, \
    ID_DELETABLE, METATHESIS_COST, pretty
import lexicon_id, lexicon_fa


class Trie:
    __slots__ = ("children", "terms")
    def __init__(self):
        self.children = {}
        self.terms = []
    def insert(self, phones, term_id):
        node = self
        for p in phones:
            node = node.children.setdefault(p, Trie())
        node.terms.append(term_id)


def build_id_trie(theme_boost=None):
    lex = lexicon_id.build()
    entries = []
    trie = Trie()
    for orth, (phones, freq) in lex.items():
        boost = (theme_boost or {}).get(orth, 1.0)
        lf = math.log(freq * boost + 1)
        entries.append({"orth": orth, "ph": phones, "lf": lf})
        trie.insert(phones, len(entries) - 1)
    return trie, entries


def build_fa_trie(theme_boost=None):
    raw = lexicon_fa.build()
    entries, trie = [], Trie()
    seen = set()
    for e in raw:
        if len(e["script"].replace("‌", "")) < 2 and e["tag"] == "lex":
            continue                      # letter-name junk (ء, آ ...)
        variants = [tuple(e["ph"])]
        if e["ph"][0] == "q" and len(e["ph"]) > 1 and is_vowel(e["ph"][1]):
            variants.append(tuple(e["ph"][1:]))   # epenthetic onset dropped
        boost = (theme_boost or {}).get(e["tr"], 1.0)
        for ph in variants:
            key = (ph, e["script"])
            if key in seen or not ph:
                continue
            seen.add(key)
            entries.append({"orth": e["script"], "tr": e["tr"], "ph": ph,
                            "lf": math.log(e["freq"] * boost + 1),
                            "tag": e["tag"], "gloss": e["gloss"]})
            trie.insert(ph, len(entries) - 1)
    return trie, entries


WORD_PENALTY = 3.5         # discourages function-word confetti
COST_WEIGHT = 2.4
LEN_BONUS = 1.2            # per phone of a closed word
SHORT_PENALTY = 3.5        # extra for 1-2 phone words
PENDING_HEURISTIC = 2.0    # beam-ranking credit per phone inside an open word
LONG = 4                   # phones for a word to count as content


def line_ok(words, entries):
    """Content requirement: enough long words, no word >2x."""
    lens = [len(entries[i]["ph"]) for i in words]
    if sum(1 for L in lens if L >= 4) < 2:
        return False
    from collections import Counter
    if Counter(words).most_common(1)[0][1] > 2:
        return False
    return True


def step_options(node, root, closing_allowed=True):
    """Next-phone options: (phone, child, closed_term_or_None)."""
    opts = [(p, ch, None) for p, ch in node.children.items()]
    if closing_allowed and node.terms and node is not root:
        best = node.terms[0]
        opts += [(p, ch, node) for p, ch in root.children.items()]
    return opts


def run(seed_targets=(9, 10, 11), beam=6000, per_key=2, max_lines=4000,
        theme_id=None, theme_fa=None, max_cost=7.5, progress=True,
        jitter=0.0, seed=0):
    import random
    rng = random.Random(seed)
    id_trie, id_entries = build_id_trie(theme_id)
    fa_trie, fa_entries = build_fa_trie(theme_fa)
    if jitter:
        for e in id_entries:
            e["lf"] += rng.uniform(-jitter, jitter)
        for e in fa_entries:
            e["lf"] += rng.uniform(-jitter, jitter)

    # State: (neg_score, cost, id_node, fa_node, id_words, fa_words,
    #         pairs, sylls, last_was_vowel, eps_streak, id_lf, fa_lf,
    #         id_wordlens, fa_wordlens)
    def initial():
        return (0.0, id_trie, fa_trie, (), (), (), 0, False, 0, 0.0, 0.0, 0, 0)

    def score(cost, id_val, fa_val):
        return (id_val + fa_val) - COST_WEIGHT * cost

    def word_value(entry):
        v = entry["lf"] + LEN_BONUS * len(entry["ph"]) - WORD_PENALTY
        if len(entry["ph"]) <= 2:
            v -= SHORT_PENALTY
        return v

    def close(words, val, node, entries):
        """Close best word at node; block loop-y reuse of words."""
        e = max(node.terms, key=lambda i: entries[i]["lf"])
        n_prev = words.count(e)
        if n_prev >= 2:
            return None
        if n_prev >= 1 and len(entries[e]["ph"]) < LONG:
            return None       # short words may not repeat at all
        return words + (e,), val + word_value(entries[e])

    completed = []
    beam_states = [initial()]
    max_pairs = 2 * max(seed_targets) + 8
    stats = {"expanded": 0, "completed_raw": 0}

    for t in range(max_pairs):
        buckets = defaultdict(list)
        for st in beam_states:
            (cost, id_node, fa_node, id_words, fa_words, pairs, sylls,
             last_v, eps, id_lf, fa_lf, did, dfa) = st
            id_opts = step_options(id_node, id_trie)
            fa_opts = step_options(fa_node, fa_trie)
            stats["expanded"] += 1

            def push(ncost, nid, nfa, niw, nfw, npairs, nsyl, nlv, neps,
                     nival, nfval, ndid, ndfa):
                if ncost > max_cost:
                    return
                key = (id(nid), id(nfa), nsyl)
                s = score(ncost, nival, nfval) \
                    + PENDING_HEURISTIC * (ndid + ndfa)
                buckets[key].append((-s, ncost, nid, nfa, niw, nfw, npairs,
                                     nsyl, nlv, neps, nival, nfval,
                                     ndid, ndfa))

            # 1. fa epsilon deletion (intervocalic ʔ/h)
            if last_v and eps == 0:
                for p, ch, closed in step_options(fa_node, fa_trie):
                    if p in FA_DELETABLE and any(is_vowel(x) for x in ch.children):
                        nfw, nfval = fa_words, fa_lf
                        if closed is not None:
                            r = close(fa_words, fa_lf, closed, fa_entries)
                            if r is None:
                                continue
                            nfw, nfval = r
                        push(cost + EPSILON_COST, id_node, ch, id_words, nfw,
                             pairs + ((None, p),), sylls, True, 1, id_lf,
                             nfval, did, 1 if closed is not None else dfa + 1)
            # id-side h deletion
            if last_v and eps == 0:
                for p, ch, closed in step_options(id_node, id_trie):
                    if p in ID_DELETABLE and any(is_vowel(x) for x in ch.children):
                        niw, nival = id_words, id_lf
                        if closed is not None:
                            r = close(id_words, id_lf, closed, id_entries)
                            if r is None:
                                continue
                            niw, nival = r
                        push(cost + EPSILON_COST, ch, fa_node, niw, fa_words,
                             pairs + ((p, None),), sylls, True, 1, nival,
                             fa_lf, 1 if closed is not None else did + 1, dfa)

            # 2. normal paired step
            for ip, ich, iclosed in id_opts:
                for fp, fch, fclosed in fa_opts:
                    c = match_cost(ip, fp)
                    if c is None:
                        continue
                    niw, nival = id_words, id_lf
                    if iclosed is not None:
                        r = close(id_words, id_lf, iclosed, id_entries)
                        if r is None:
                            continue
                        niw, nival = r
                    nfw, nfval = fa_words, fa_lf
                    if fclosed is not None:
                        r = close(fa_words, fa_lf, fclosed, fa_entries)
                        if r is None:
                            continue
                        nfw, nfval = r
                    v = is_vowel(ip)
                    push(cost + c, ich, fch, niw, nfw, pairs + ((ip, fp),),
                         sylls + (1 if v else 0), v, 0, nival, nfval,
                         1 if iclosed is not None else did + 1,
                         1 if fclosed is not None else dfa + 1)

            # 3. metathesis: id (V,h) ~ fa (h,V')
            for ip, ich, iclosed in id_opts:
                if not is_vowel(ip):
                    continue
                for ih, ich2, iclosed2 in step_options(ich, id_trie):
                    if ih != "h":
                        continue
                    for fp, fch, fclosed in fa_opts:
                        if fp != "h":
                            continue
                        for fv, fch2, fclosed2 in step_options(fch, fa_trie):
                            if not is_vowel(fv):
                                continue
                            vc = match_cost(ip, fv)
                            if vc is None:
                                continue
                            niw, nival = id_words, id_lf
                            bad = False
                            for cl in (iclosed, iclosed2):
                                if cl is not None:
                                    r = close(niw, nival, cl, id_entries)
                                    if r is None:
                                        bad = True
                                        break
                                    niw, nival = r
                            if bad:
                                continue
                            nfw, nfval = fa_words, fa_lf
                            for cl in (fclosed, fclosed2):
                                if cl is not None:
                                    r = close(nfw, nfval, cl, fa_entries)
                                    if r is None:
                                        bad = True
                                        break
                                    nfw, nfval = r
                            if bad:
                                continue
                            ndid = did + 2 if iclosed is None and \
                                iclosed2 is None else 1
                            ndfa = dfa + 2 if fclosed is None and \
                                fclosed2 is None else 1
                            push(cost + METATHESIS_COST + vc, ich2, fch2,
                                 niw, nfw,
                                 pairs + (("META", ip, ih, fp, fv),),
                                 sylls + 1, False, 0, nival, nfval,
                                 ndid, ndfa)

        # prune: per-key, then stratified by content-word progress
        nxt = []
        for key, cands in buckets.items():
            cands.sort(key=lambda x: x[0])
            nxt.extend(cands[:per_key])
        def stratum(st):
            iw, fw = st[4], st[5]
            li = sum(1 for i in iw if len(id_entries[i]["ph"]) >= LONG)
            lf_ = sum(1 for i in fw if len(fa_entries[i]["ph"]) >= LONG)
            return min(li, lf_, 3)
        strata = defaultdict(list)
        for st in nxt:
            strata[stratum(st)].append(st)
        chosen = []
        quota = max(beam // 4, 1)
        leftovers = []
        for s_key, group in strata.items():
            group.sort(key=lambda x: x[0])
            chosen.extend(group[:quota])
            leftovers.extend(group[quota:])
        if len(chosen) < beam:
            leftovers.sort(key=lambda x: x[0])
            chosen.extend(leftovers[:beam - len(chosen)])
        chosen.sort(key=lambda x: x[0])
        beam_states = []
        for st in chosen[:beam]:
            (_neg, cost, id_node, fa_node, id_words, fa_words, pairs, sylls,
             last_v, eps, id_lf, fa_lf, did, dfa) = st
            beam_states.append((cost, id_node, fa_node, id_words, fa_words,
                                pairs, sylls, last_v, eps, id_lf, fa_lf,
                                did, dfa))
            # completion check
            if sylls in seed_targets and id_node.terms and fa_node.terms \
                    and id_node is not id_trie and fa_node is not fa_trie:
                ri = close(id_words, id_lf, id_node, id_entries)
                rf = close(fa_words, fa_lf, fa_node, fa_entries)
                if ri is None or rf is None:
                    continue
                fiw, ival = ri
                ffw, fval = rf
                if not line_ok(fiw, id_entries) or not line_ok(ffw, fa_entries):
                    continue
                s = score(cost, ival, fval)
                completed.append((s, cost, fiw, ffw, pairs, sylls))
                stats["completed_raw"] += 1
        if progress and t % 5 == 0:
            both_term = sum(1 for s in beam_states
                            if s[1].terms and s[2].terms)
            syl_hits = sum(1 for s in beam_states if s[6] in seed_targets)
            print(f"  step {t}: beam={len(beam_states)} both_term={both_term}"
                  f" syl_in_target={syl_hits} completed={len(completed)}",
                  file=sys.stderr)
            if os.environ.get("SEARCH_DEBUG") and beam_states:
                for s in beam_states[:3]:
                    print("   id:", [id_entries[i]['orth'] for i in s[3]],
                          "fa:", [fa_entries[i]['tr'] for i in s[4]],
                          "cost", s[0], "syl", s[6], file=sys.stderr)
        if not beam_states:
            break

    completed.sort(key=lambda x: -x[0])
    # dedupe: best line per (id segmentation, fa segmentation)
    seen, out = set(), []
    for line in completed:
        key = (line[2], line[3])
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
    return out[:max_lines], id_entries, fa_entries, stats


def render_line(line, id_entries, fa_entries):
    s, cost, iw, fw, pairs, sylls = line
    id_txt = " ".join(id_entries[i]["orth"] for i in iw)
    fa_txt = " ".join(fa_entries[i]["orth"] for i in fw)
    fa_tr = " ".join(fa_entries[i]["tr"] for i in fw)
    ipa_id, ipa_fa, notes = [], [], []
    for p in pairs:
        if p[0] == "META":
            _, ip, ih, fp, fv = p
            ipa_id += [ip, ih]; ipa_fa += [fp, fv]
            notes.append(f"metathesis {ip}+h ~ h+{fv} (cost {METATHESIS_COST}"
                         f"{'+1' if ip != fv else ''})")
        elif p[0] is None:
            ipa_fa.append(p[1]); notes.append(f"fa /{p[1]}/ deleted (cost 1)")
        elif p[1] is None:
            ipa_id.append(p[0]); notes.append(f"id /{p[0]}/ deleted (cost 1)")
        else:
            ipa_id.append(p[0]); ipa_fa.append(p[1])
            c = match_cost(p[0], p[1])
            if c:
                notes.append(f"{p[0]}~{p[1]} (cost {c})")
    return {"score": round(s, 2), "cost": cost, "sylls": sylls,
            "id": id_txt, "fa": fa_txt, "fa_tr": fa_tr,
            "ipa_id": pretty(ipa_id), "ipa_fa": pretty(ipa_fa),
            "notes": notes,
            "fa_tags": [fa_entries[i]["tag"] for i in fw],
            "fa_gloss": [fa_entries[i]["gloss"] for i in fw]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--beam", type=int, default=6000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-lines", type=int, default=4000)
    ap.add_argument("--theme-id", default=None, help="JSON file word->boost")
    ap.add_argument("--theme-fa", default=None)
    ap.add_argument("--jitter", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    ti = json.load(open(args.theme_id)) if args.theme_id else None
    tf = json.load(open(args.theme_fa)) if args.theme_fa else None
    lines, ide, fae, stats = run(beam=args.beam, max_lines=args.max_lines,
                                 theme_id=ti, theme_fa=tf,
                                 jitter=args.jitter, seed=args.seed)
    print("stats:", stats, file=sys.stderr)
    out = [render_line(l, ide, fae) for l in lines]
    if args.out:
        json.dump(out, open(args.out, "w"), ensure_ascii=False, indent=1)
    for r in out[:30]:
        print(json.dumps(r, ensure_ascii=False))
