# Bilingual Phonetic Poem: Indonesian ⟺ Persian

A search pipeline that produces a poem consisting of a single phoneme
stream readable **simultaneously** as a coherent Indonesian poem and a
coherent Persian poem — with different word boundaries and different
meanings. (A two-sided homophonic poem: unlike van Rooten's
*Mots d'Heures*, both readings must be real text.)

Deliverables:
- `poem.md` — the poem: IPA / Indonesian / Persian (script + translit),
  with per-line accent-cost annotations and the blind audit table.
- `report.md` — lexicon sizes, search funnel statistics, judge scores,
  iteration story, and rejected alternatives.
- `src/` — the runnable search + scoring code (this file explains how).
- `results/` — machine-readable artifacts: all 38 judge-passing lines
  (`survivors.json`), the assembled poem (`final_poem.json`), blind
  audits, coherence judgment, and rejected-alternative exhibits.

## Pipeline

```
data/            WikiPron IPA (Wiktionary-scraped) + OpenSubtitles
                 frequency lists, downloaded from GitHub mirrors
src/phonespace.py   compromise phoneme space + accent-cost table
src/lexicon_id.py   Indonesian lexicon (rule G2P + WikiPron for /e/-vs-/ə/)
src/lexicon_fa.py   Persian lexicon (classical→Iranian canonicalization,
                    programmatic verb inflection + enclitics)
src/search.py       product-trie beam search over the two lexicons
src/generate.py     multi-run driver (jitter restarts, attractor banning,
                    diversified top-K)
src/judge.py        LLM judging: batch prep / merge / optional direct API
src/assemble.py     poem assembly with diversity + loanword caps
```

### 1. Get data

```
cd data
curl -sSO https://raw.githubusercontent.com/CUNY-CL/wikipron/master/data/scrape/tsv/fas_arab_broad.tsv
curl -sSO https://raw.githubusercontent.com/CUNY-CL/wikipron/master/data/scrape/tsv/ind_latn_broad.tsv
curl -sS -o id_freq_50k.txt https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/id/id_50k.txt
curl -sS -o fa_freq_50k.txt https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/fa/fa_50k.txt
curl -sS -o en_freq_50k.txt https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/en_50k.txt
```

(The original plan called for kaikki.org Wiktionary JSON; that host was
unreachable from the build environment, so WikiPron — the same Wiktionary
pronunciation data, scraped and normalized by CUNY-CL — is used instead.
The English list filters English junk out of the OpenSubtitles Indonesian
list.)

### 2. Generate candidates

```
cd src
python3 generate.py --out ../data/build/candidates.json \
    --beam 5000 --runs 9 --jitter 2.5 --top 1400 \
    --theme-id ../data/build/theme_id.json \
    --theme-fa ../data/build/theme_fa.json
```

Theme files are optional `{word: boost}` JSON maps (Indonesian orthography
/ Persian base transliteration) that multiply word frequencies, biasing
the search toward a semantic field. Weights for the proxy score live at
the top of `search.py` (`WORD_PENALTY`, `COST_WEIGHT`, `LEN_BONUS`, …);
the accent-cost table is in `phonespace.py`.

### 3. Judge

```
python3 judge.py prepare ../data/build/candidates.json ../data/build/judge_round1
# then EITHER (with an API key):
ANTHROPIC_API_KEY=... python3 judge.py api ../data/build/judge_round1
# OR have any capable LLM read each batch_*.json (instructions are
# embedded in the file) and write the JSON array to scores_*.json.
python3 judge.py merge ../data/build/candidates.json \
    '../data/build/judge_round1/scores_*.json' ../data/build/judged.json
```

The M/G scales, the G≥3 hard floor, and the combined line score
`min(M) + 0.7·avg(M) + 0.5·(G_id+G_fa) + 2.0·A` follow the task
specification; `A = 1/(1 + cost/syllable)`.

### 4. Assemble

```
python3 assemble.py ../data/build/judged.json ../data/build/poems.json -n 20
```

Emits three assemblies (top / strict / diverse) for a final poem-level
coherence judgment.

## The accent model

See `phonespace.py` for the full table. Highlights (cost per instance):
id /a/ ~ fa /ɒː/ = 1; id /ə/ ~ fa /e/ = 1; id /u/ ~ fa /o/ = 1
(required by the spec's own dua ~ do'â example); intervocalic deletion of
fa /ʔ/ or /h/ = 1; the tanah ~ tanhâ V+h/h+V metathesis = 1 + vowel cost;
fa /q~ɣ/ ~ id /k,g/ = 2; other consonant mismatches forbidden. Vowels only
match vowels, so syllable counts agree by construction. Persian is read in
the **formal Iranian** register (WikiPron classical transcriptions are
mapped: short i→e, short u→o, iː→i, uː→u, eː→e, oː→o, aː→â).

## Notes

- A calibration check: the task's own worked example
  (*dua tanah mandi* ~ *do'â tanhâ mândi*) costs **6.0** under this
  table (3× a~â, u~o, one ʔ-deletion, one metathesis) — so the stated
  ≤1.5/line budget is aspirational; the search treats cost as a soft
  axis exactly as specified.
- Indonesian words containing <e> are admitted only when WikiPron marks
  the /e/-vs-/ə/ distinction or a known prefix decomposition does;
  the pipeline never guesses schwa.
- Persian entries lacking usable IPA are dropped, never guessed from
  script.
