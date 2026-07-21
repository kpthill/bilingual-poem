"""Compromise phoneme space and accent-cost model.

Canonical phone inventories after normalization:

Indonesian (id): vowels {a e i o u @} (@ = schwa), consonants
  {p b t d k g m n ng ny s z l r f h sh zh ch jh j w x q(=glottal)}.
  We write multi-char phones with ASCII names: ng=/ŋ/ ny=/ɲ/ sh=/ʃ/ zh=/ʒ/
  ch=/tʃ/ jh=/dʒ/ q=/ʔ/.

Persian (fa), formal Iranian reading: vowels {a e i o u A} (A = /ɒː/ â),
  consonants {p b t d k g m n s z l r f v h sh zh ch jh j x G(=q/ɣ) q(=ʔ)}.

Costs follow the task spec table; additions needed by the spec's own worked
example (dua/do'â, tanah/tanhâ) are marked ADD.
"""

VOWELS = set("aeiou@A")

def is_vowel(p):
    return p in VOWELS

# id phone, fa phone -> cost. Missing pair = forbidden (None).
# Symmetric pairs listed once; lookup tries both orders where marked.
_VOWEL_COST = {
    ("a", "a"): 0.0,   # id /a/ ~ fa /æ/ : free per spec
    ("a", "A"): 1.0,   # id /a/ ~ fa /ɒː/ (â): the big systematic one
    ("@", "e"): 1.0,   # id schwa ~ fa /e/
    ("@", "a"): 2.0,   # not in spec table; audible but parseable
    ("e", "e"): 0.0,
    ("i", "i"): 0.0,
    ("o", "o"): 0.0,
    ("u", "u"): 0.0,
    ("u", "o"): 1.0,   # ADD: required by spec example dua ~ do'â
    ("o", "u"): 1.0,
    ("e", "i"): 1.5,
    ("i", "e"): 1.5,
}

_CONS_COST = {}
for c in ["p","b","t","d","k","g","m","n","s","z","l","r","f","h",
          "sh","zh","ch","jh","j","x","q","ng"]:
    _CONS_COST[(c, c)] = 0.0
_CONS_COST.update({
    ("w", "v"): 1.0,   # Persian /v/ is [ʋ~w]-ish; id has no /v/
    ("w", "w"): 0.0,
    ("k", "G"): 2.0,   # fa q/ɣ ~ id k (spec: cost 2)
    ("g", "G"): 2.0,   # fa q/ɣ ~ id g (spec: cost 2)
    ("k", "x"): 2.0,   # fa x ~ id k, beyond spec's q/ɣ line but same family
    ("k", "q"): 1.0,   # id final k is [ʔ]; ~ fa glottal stop
    ("ny", "n"): 3.0,  # effectively discouraged
    ("f", "p"): 3.0,
})

def match_cost(id_ph, fa_ph):
    """Cost of realizing id phone and fa phone as one shared segment.
    Returns None if forbidden."""
    iv, fv = is_vowel(id_ph), is_vowel(fa_ph)
    if iv != fv:
        return None                      # preserves syllable-count equality
    table = _VOWEL_COST if iv else _CONS_COST
    return table.get((id_ph, fa_ph))

# Epsilon rules: fa /ʔ/ or /h/ may be deleted (matched against nothing on the
# Indonesian side) when intervocalic in the shared stream; likewise an
# Indonesian intervocalic /h/ may be absent on the Persian side. Cost 1.
EPSILON_COST = 1.0
FA_DELETABLE = {"q", "h"}   # fa ʔ, h
ID_DELETABLE = {"h"}

# Metathesis: id (V, h) ~ fa (h, V') — the tanah/tanhâ pattern. Cost 1 plus
# the vowel-pair cost. Handled specially in the search.
METATHESIS_COST = 1.0

PRETTY_IPA = {
    "a":"a","e":"e","i":"i","o":"o","u":"u","@":"ə","A":"aː",
    "p":"p","b":"b","t":"t","d":"d","k":"k","g":"ɡ","m":"m","n":"n",
    "ng":"ŋ","ny":"ɲ","s":"s","z":"z","l":"l","r":"r","f":"f","v":"v",
    "h":"h","sh":"ʃ","zh":"ʒ","ch":"tʃ","jh":"dʒ","j":"j","w":"w",
    "x":"x","q":"ʔ","G":"ɣ",
}

def pretty(stream):
    return " ".join(PRETTY_IPA.get(p, p) for p in stream)

def syllables(stream):
    return sum(1 for p in stream if is_vowel(p))
