"""POS maps and POS-bigram language models from UD treebanks.

Gives the beam search a cheap syntax prior: each closed word contributes
log P(UPOS | previous UPOS), estimated from UD_Persian-Seraji /
UD_Indonesian-GSD, with BOS/EOS transitions. Words without a treebank POS
get category "X" (smoothed)."""
import os, math
from collections import Counter, defaultdict

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

def _load(path, norm=None):
    word_pos = defaultdict(Counter)
    bigrams = Counter()
    unigrams = Counter()
    prev = "BOS"
    with open(path, encoding="utf8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            if not line.strip():
                bigrams[(prev, "EOS")] += 1
                unigrams[prev] += 1
                prev = "BOS"
                continue
            cols = line.split("\t")
            if len(cols) < 4 or not cols[0].isdigit():
                continue
            w, pos = cols[1], cols[3]
            if pos in ("PUNCT", "SYM"):
                continue
            if norm:
                w = norm(w)
            word_pos[w][pos] += 1
            bigrams[(prev, pos)] += 1
            unigrams[prev] += 1
            prev = pos
    wp = {w: c.most_common(1)[0][0] for w, c in word_pos.items()}
    tags = set(p for _, p in bigrams) | set(p for p, _ in bigrams)
    logp = {}
    V = len(tags) + 1
    for p in list(unigrams) + ["BOS"]:
        tot = unigrams.get(p, 0)
        for q in tags:
            logp[(p, q)] = math.log((bigrams.get((p, q), 0) + 0.5) /
                                    (tot + 0.5 * V))
    return wp, logp

class PosLM:
    def __init__(self, lang):
        if lang == "fa":
            from lexicon_fa import ar_norm
            self.wp, self.logp = _load(os.path.join(DATA, "fa_ud.conllu"),
                                       norm=ar_norm)
        else:
            self.wp, self.logp = _load(os.path.join(DATA, "id_ud.conllu"),
                                       norm=str.lower)
        self.default = math.log(1e-3)

    def pos_of(self, word):
        return self.wp.get(word, "X")

    def trans(self, prev_pos, pos):
        return self.logp.get((prev_pos, pos), self.default)

if __name__ == "__main__":
    fa = PosLM("fa")
    idn = PosLM("id")
    print("fa vocab:", len(fa.wp), "id vocab:", len(idn.wp))
    for w in ["دل", "رفت", "با", "تنها"]:
        print(w, fa.pos_of(w))
    for w in ["tanah", "mandi", "yang", "dua"]:
        print(w, idn.pos_of(w))
    print("fa P(VERB|NOUN):", fa.trans("NOUN", "VERB"),
          "P(EOS|VERB):", fa.trans("VERB", "EOS"))
