# Search Report: Indonesian/Persian Phonetically Dual Poem

Companion to `poem.md` (the deliverable) and `README.md` (how to re-run).
All numbers below are from the actual run that produced the poem
(July 22, 2026, in the Claude Code remote environment).

## Result in one paragraph

The final poem has **10 lines** (the brief asked for ~20; the honest-N
clause was invoked — see *Limitations*). Every line passed a strict LLM
judge floor of grammaticality ≥ 3/5 **in both languages**, poem-level
coherence was judged **4/5 for the Indonesian reading and 4/5 for the
Persian reading** by a critic who saw the sides separately, and the total
accent cost is **21.0 over 71 syllables (0.30/syllable)** — for
calibration, the task's own worked example (*dua tanah mandi* ~ *do'â
tanhâ mândi*) costs 1.20/syllable under the same table.

## Data sources actually used

The build environment's network policy blocked kaikki.org, Wiktionary,
Leipzig, and HuggingFace. Substitutions (same underlying data, different
mirror):

| Planned | Used |
|---|---|
| kaikki.org Wiktionary JSON (Persian IPA) | WikiPron `fas_arab_broad.tsv` (CUNY-CL's Wiktionary pronunciation scrape), 10,312 rows |
| Wiktionary Indonesian schwa-marked list | WikiPron `ind_latn_broad.tsv`, 18,590 rows |
| Leipzig/OpenSubtitles frequency lists | hermitdave FrequencyWords (OpenSubtitles 2018) id/fa/en 50k lists |
| — | UD_Persian-Seraji + UD_Indonesian-GSD treebanks (added mid-run, see *Iteration story*) |

## Lexicon sizes

| | entries | notes |
|---|---|---|
| Indonesian surface lexicon | **16,255** | top-30k OpenSubtitles forms ∩ (WikiPron ∪ rule-G2P for e-less words ≥5 letters ∪ prefix decomposition); English-wordlist junk filter; words with ambiguous <e> admitted only via WikiPron or known-prefix schwa |
| Persian base entries (usable IPA, freq-joined) | 6,387 | WikiPron rows canonicalized classical→formal-Iranian (majhul mapping), style detected per row |
| Persian after programmatic inflection | **49,816** | verb conjugations from 35 curated stem pairs (past/present × mi-/na-/be- × 6 endings + participle), copula/possessive enclitics, plural -hâ/-ân, ezâfe, indefinite -i |
| Persian trie entries | 56,523 | + zero-cost variants with epenthetic initial /ʔ/ dropped |

## The search funnel

| stage | count |
|---|---|
| beam-search runs (8 generation rounds, varying constraints/themes/jitter) | 88 |
| raw completed lines (dual-segmentable, pre-dedup) | **19,687** |
| after per-run dedup + diversified selection (word-frequency caps) | 3,286 |
| unique lines sent to the LLM judge | **1,711** |
| passed the dual G ≥ 3 floor | **38 (2.7%)** |
| assembled by the poet-editor pass | 12 |
| survived blind audit + coherence cuts → final poem | **10** |

Cheap-filter rejection rate ahead of the judge: 1 − 1,711/19,687 = **91.3%**
by count of raw lines (99.99%+ of the lattice's implicit search space never
became a completed line at all). Judge spend: ~50 batched subagent calls
covering 2,040 line-judgments (1,711 unique + pilot round).

### Per-side pass rates (why Persian is the bottleneck)

Across the 1,382 judged lines of the main + refinement rounds:
G_id ≥ 3: **322 (23.3%)** — G_fa ≥ 3: **122 (8.8%)** — both: **38 (2.7%)**.
An earlier 329-line round with no syntactic guidance scored G_id ≥ 3 at
8.2% and G_fa ≥ 3 at **0%**, which forced the mid-run redesign below.

## Iteration story (what the judge feedback changed)

1. **Round 1-3 (pure frequency proxy):** 0/329 dual passes. Judges:
   Persian side is "word salad with stranded function words"; clause-initial
   *râ*, ezâfe hung on finite verbs, ghost archaisms (*ar*, *andar*, *hin*).
2. **Fixes:** Persian-verb-final search mode (Persian poetry is verb-final);
   ban clause-initial clitics; ghost-word blocklist from judge flags;
   no-suffix list for closed-class words and finite verbs; shorter
   line targets (5-8 syllables — the task's own gold example is 5).
3. **POS prior:** UD-treebank POS-bigram LMs for both languages added to
   the beam score (each word closure pays log P(POS|prev POS); line end
   pays P(EOS|POS)). This is what finally made Persian G ≥ 3 reachable
   (0% → 8.8%).
4. **Theme rounds:** after the first survivors appeared, their vocabulary
   families (*tanah/tanhâ*, *ada malam/'adam 'âlam*, *desa/sadâ*,
   *rumah/ru mâh*, *dasar/'asar*) were boosted 30-40× and the search
   re-run, yielding 13 more passes (the "densifying" round).

## Top-5 rejected alternatives for three sample lines

Showing the search explored genuine alternatives (M/G = meaning/grammar,
Indonesian then Persian; the winner is the line in the poem):

**Winner: `doa jadi desa buram` / `do'â jâ dide, sabur-am`**

| alternative | M | G | fate |
|---|---|---|---|
| doa jadi debu dasar / do'â jâ did-e bud 'asar | 3,3 | 4,3 | passed, cut in assembly (loan-flagged *doa*) |
| doa jadi drum alam / do'â jâ did ru mâl-am | 4,2 | 4,2 | rejected: FA second half collapses |
| doa jadi dewa licin / do'â jâ did-e vali chin | 4,2 | 4,2 | rejected: strong ID image, FA tail disjoint |
| doa jadi desa mari / do'â jâ did-e samar-i | 2,3 | 3,3 | passed, lower score |
| doa jadi drum anda / do'â jâ did ru mânda | 3,2 | 4,2 | rejected: FA loose |

**Winner: `tanah tanah rumah` / `tanhâ tanhâ ru mâh`** (the closing line)

| alternative | M | G | fate |
|---|---|---|---|
| tanah tanah tanam / tanhâ tanhâ tan-am | 2,4 | 3,4 | passed; editor preferred *ru mâh* ending |
| tanah tanah tiram / tanhâ tanhâ tir-am | 2,4 | 3,4 | passed; same family |
| tanah tanah tadi drum / tanhâ tanhâ tâ did rum | 2,3 | 3,3 | passed; *drum* weakens ID |
| tanah tanah rumah / tanhâ tanhâ ro mâh | 2,3 | 3,3 | passed; colloquial *ro* variant |
| tanah tanah tadi enam / tanhâ tanhâ tâ din-am | 3,2 | 3,2 | rejected: FA verbless trail |

**Winner: `rusa dan abu di rumah` / `ro, sadâ nabudi ru mah`**

| alternative | M | G | fate |
|---|---|---|---|
| rusa dan ayam / ru sadâ nay-am | 3,3 | 4,3 | passed, also in poem (different family member) |
| rusa dan abu di badan / ru sadâ nabud-i badan | 3,2 | 4,2 | rejected: *badan* shared loan, FA tail unlinked |
| rusa dan abu ditanam / ru sadâ nabud-i tan-am | 4,1 | 4,2 | rejected: striking ID passive, FA pieces don't join |
| rusa dan imam / ru sadâ nim-am | 3,2 | 4,3 | passed, weaker M_fa |
| rusa dan awam / ru sadâ nav-am | 3,2 | 4,3 | passed, weaker M_fa |

## Final audits

- **Poem-level coherence (blind per side): Indonesian 4/5** ("a genuinely
  unified village-day poem — dawn prayer to night, resolving in the
  closing chant"), **Persian 4/5** ("a recognizably single Sufi lyric of
  annihilation... with the Rumi allusion (nay + Rum) rewarding a close
  reader").
- **Blind recoverability** (auditors saw only IPA, no intended readings):
  Indonesian ear **3.8/5** on the kept lines — every kept line's words were
  recovered; Persian ear **2.1/5** — real Persian words surface
  (*do'â, sadâ, tanhâ, mâh*) but full clauses often need the segmentation
  supplied. Two lines that failed audits (a line whose Indonesian relied on
  colloquial /nam/ for *enam*, and the noun-pile *roda darah ekor*) were
  **cut** from the assembled 12; the asymmetry that remains is reported,
  not hidden.

## Limitations (the honest-N clause)

- **10 lines, not 20.** The dual-grammaticality intersection at this
  lexicon size supports roughly 38 usable lines, many of them
  family-variants of each other. Padding to 20 would have meant including
  lines the judge scored G=2. Per the brief, 10 good lines beat 20
  mediocre ones.
- **Persian cold-recoverability is the weak axis** (2.1/5 blind). The
  Persian reading is grammatical and coherent *given* the segmentation;
  a cold listener catches words but not always clauses. A human Persian
  poet could likely close this gap with hand-polishing — the pipeline
  only asserts what its judges verified.
- **Judge variance:** M/G scores are single-pass per line (one judge per
  batch). Borderline G=2/G=3 calls decide survival; a 3-vote panel would
  firm up the floor (the code supports re-running with more batches).
- Line 2's *nay-am* spelling نی‌ام and line 3's *mah* (poetic short form
  of *mâh*) were verified by the editor pass; *enam*→/nam/ (colloquial
  clipped six) was cut with its line.
- Shared loanwords: the final poem uses **zero** loan-flagged lines
  (*doa/do'â* appears in line 1 but the readings diverge — "prayer becomes
  a blurred village" vs "the prayer has found its place; I am patient" —
  the judge did not flag it; the flagged *salam/salâm* and *debu bud*
  lines were excluded in assembly).
