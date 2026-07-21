"""Indonesian lexicon: frequency list + WikiPron IPA + rule-based G2P.

Policy on the /e/ vs /ə/ ambiguity (both written <e>): a word containing <e>
is only admitted if (a) WikiPron has it, (b) it decomposes into a known
prefix (whose <e> is schwa) + an admissible root, or (c) the <e> sits only in
a curated closed-class word. We never guess.
"""
import re, unicodedata, os

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

WIKIPRON_MAP = {
    "a":"a","i":"i","u":"u","e":"e","ɛ":"e","ə":"@","o":"o","ɔ":"o",
    "ʊ":"u","ɪ":"i","aː":"a","ä":"a","ɑ":"a",
    "t̚":"t","k̚":"k","p̚":"p","ʔ̚":"q","ʔ":"q",
    "i̯":"j","u̯":"w","a̯":"w",
    "t͡ʃ":"ch","d͡ʒ":"jh","ŋ":"ng","ɲ":"ny","ʃ":"sh","ʒ":"zh",
    "x":"x","j":"j","w":"w","p":"p","b":"b","t":"t","d":"d","k":"k",
    "ɡ":"g","g":"g","m":"m","n":"n","s":"s","z":"z","l":"l","r":"r",
    "f":"f","v":"f","h":"h","t̪":"t","n̪":"n","ɾ":"r","q":"k",
}

PREFIXES = [  # prefix orthography -> phones (all <e> here are schwa)
    ("meng","m @ ng"),("meny","m @ ny"),("mem","m @ m"),("men","m @ n"),
    ("me","m @"),("peng","p @ ng"),("peny","p @ ny"),("pem","p @ m"),
    ("pen","p @ n"),("per","p @ r"),("pe","p @"),("ber","b @ r"),
    ("bel","b @ l"),("be","b @"),("ter","t @ r"),("se","s @"),
    ("ke","k @"),("di","d i"),
]
SUFFIXES = [("kan","k a n"),("nya","ny a"),("lah","l a h"),("kah","k a h"),
            ("ku","k u"),("mu","m u"),("an","a n"),("i","i")]

def load_wikipron():
    lex = {}
    with open(os.path.join(DATA, "ind_latn_broad.tsv"), encoding="utf8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 2:
                continue
            word, ipa = parts[0].lower(), parts[1].split(" ")
            phones = []
            ok = True
            for p in ipa:
                p2 = WIKIPRON_MAP.get(p)
                if p2 is None:
                    ok = False
                    break
                phones.append(p2)
            if ok and word not in lex:      # first pronunciation wins
                lex[word] = phones
    return lex

def g2p_rule(word):
    """Rule-based G2P for words WITHOUT <e>. Returns phones or None."""
    if not re.fullmatch(r"[a-z-]+", word) or "e" in word:
        return None
    w = word.replace("-", "")
    out, i, n = [], 0, len(w)
    while i < n:
        rest = w[i:]
        if rest.startswith("ngg"): out += ["ng","g"]; i += 3; continue
        if rest.startswith("ng"): out.append("ng"); i += 2; continue
        if rest.startswith("ny"): out.append("ny"); i += 2; continue
        if rest.startswith("sy"): out.append("sh"); i += 2; continue
        if rest.startswith("kh"): out.append("x"); i += 2; continue
        # word-final diphthongs
        if rest in ("ai",): out += ["a","j"]; break
        if rest in ("au",): out += ["a","w"]; break
        if rest in ("oi",): out += ["o","j"]; break
        c = w[i]
        m = {"c":"ch","j":"jh","y":"j","v":"f","q":"k","x":"k"}
        if c in m: out.append(m[c])
        elif c in "aiou": out.append(c)
        elif c in "pbtdkgmnszlrfhw": out.append(c)
        else: return None
        i += 1
    return out

def phonotactic_ok(phones):
    """Reject un-Indonesian clusters (mostly filters English junk)."""
    from phonespace import is_vowel
    if not any(is_vowel(p) for p in phones):
        return False
    run = 0
    for p in phones:
        run = 0 if is_vowel(p) else run + 1
        if run > 2:
            return False
    return True

BLOCKLIST = {
    "ah","oh","uh","eh","er","hm","mm","ha","he","ho","hah","heh","huh",
    "hei","um","ung","ini-","itu-","ok","oke","it","or","and","the","you",
    "is","in","on","no","so","do","go","to","of","at","we","he","be","me",
    "my","up","us","was","are","for","not","but","all","one","two","who",
    "out","now","get","got","let","hey","wow","ya-","a-","i-","u-","e-",
    "aa","ii","uu","oo","ee","mmm","hmm","ohh","ahh","uhh",
}
SHORT_WHITELIST = {  # <=3 letters admitted only from here
    "di","ke","ku","mu","dan","dia","aku","kau","itu","ini","ada","air",
    "api","apa","ibu","isi","hal","tak","pun","kai","mau","mata","dua",
    "doa","ia","ya","tua","suka","laut","abu","asa","hari","tanya","bau",
    "bumi","batu","kata","kita","lagu","luka","satu","tiga","lima","kali",
    "asap","asin","aduh","raja","rasa","jika","tapi","bila","para","sang",
    "yang","dari","malu","rindu","duka","sunyi","tidur","jalan","makan",
}

def load_english(top=20000):
    out = set()
    path = os.path.join(DATA, "en_freq_50k.txt")
    if os.path.exists(path):
        with open(path, encoding="utf8") as f:
            for i, line in enumerate(f):
                if i >= top:
                    break
                out.add(line.split()[0])
    return out

def build(max_rank=30000, min_freq=40):
    wp = load_wikipron()
    english = load_english()
    lex = {}   # orth -> (phones, freq)
    with open(os.path.join(DATA, "id_freq_50k.txt"), encoding="utf8") as f:
        for rank, line in enumerate(f):
            if rank >= max_rank:
                break
            try:
                word, freq = line.split()
                freq = int(freq)
            except ValueError:
                continue
            if freq < min_freq:
                break
            word = word.lower()
            if not re.fullmatch(r"[a-z]+", word) or len(word) < 2:
                continue
            if word in BLOCKLIST:
                continue
            if len(word) <= 3 and word not in SHORT_WHITELIST:
                continue
            # English subtitle bleed-through: a word not attested as
            # Indonesian in Wiktionary but common in English is junk
            if word not in wp and word in english:
                continue
            phones = None
            if word in wp:
                phones = wp[word]
            elif "e" not in word:
                phones = g2p_rule(word)
            else:
                # try prefix/suffix decomposition; prefix <e> is schwa
                for pre, pph in PREFIXES:
                    if word.startswith(pre) and len(word) > len(pre) + 2:
                        root = word[len(pre):]
                        rp = wp.get(root) or g2p_rule(root)
                        if rp is None:
                            for suf, sph in SUFFIXES:
                                if root.endswith(suf) and len(root) > len(suf) + 2:
                                    r2 = root[:-len(suf)]
                                    r2p = wp.get(r2) or g2p_rule(r2)
                                    if r2p is not None:
                                        rp = r2p + sph.split()
                                        break
                        if rp is not None:
                            phones = pph.split() + rp
                            break
            if phones and phonotactic_ok(phones):
                lex[word] = (phones, freq)
    # ensure high-value function words present
    extras = {
        "dan":"d a n","di":"d i","ke":"k @","yang":"j a ng","itu":"i t u",
        "ini":"i n i","dari":"d a r i","tak":"t a k","pun":"p u n",
        "sang":"s a ng","para":"p a r a","dua":"d u a","tanah":"t a n a h",
        "mandi":"m a n d i","air":"a i r","laut":"l a u t",
    }
    for w, ph in extras.items():
        if w not in lex:
            lex[w] = (ph.split(), 1000)
    return lex

if __name__ == "__main__":
    lex = build()
    print("Indonesian lexicon size:", len(lex))
    for w in ["dua","tanah","mandi","yang","mereka","menangis","senja","embun"]:
        print(w, lex.get(w))
