"""Persian lexicon: WikiPron IPA canonicalized to formal Iranian reading,
frequency-joined, plus programmatic inflection (verb endings, copula
enclitics, plural, ezâfe, pronominal enclitics).

WikiPron's fas_arab_broad mixes transcription styles (Classical/Dari rows
with aː iː uː eː oː w; Iranian rows with ɒː æ e o v). We detect the style per
row and normalize everything to the formal Iranian system:
  vowels {a(=æ) e i o u A(=ɒː 'â')};   majhul mapping for classical rows:
  short i -> e, short u -> o, iː -> i, uː -> u, eː -> e, oː -> o, aː -> A.
"""
import os, re, unicodedata

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

CLASSICAL_MARKERS = {"aː","iː","uː","eː","oː","w","xʷ"}
IRANIAN_MARKERS = {"ɒː","æ","v"}

COMMON = {  # style-independent
    "b":"b","p":"p","t":"t","d":"d","k":"k","ɡ":"g","g":"g","m":"m","n":"n",
    "s":"s","z":"z","l":"l","r":"r","ɾ":"r","f":"f","h":"h","x":"x",
    "ʃ":"sh","ʒ":"zh","t͡ʃ":"ch","d͡ʒ":"jh","j":"j","ʔ":"q",
    "q":"G","ɣ":"G","ɢ":"G","v":"v","w":"v","xʷ":"x",
    "t̪":"t","d̪":"d","‿":None,"~":None,
}
CLASSICAL_V = {"a":"a","aː":"A","i":"e","iː":"i","u":"o","uː":"u",
               "eː":"e","oː":"o","æ":"a","ɒː":"A","e":"e","o":"o"}
IRANIAN_V   = {"a":"a","aː":"A","ɒː":"A","ɒ":"A","æ":"a","e":"e","i":"i",
               "o":"o","u":"u","ɛ":"e","ʊ":"o","ɪ":"e","ə":"e"}

def canon_row(ipa_tokens):
    style_cl = any(t in CLASSICAL_MARKERS for t in ipa_tokens)
    style_ir = any(t in IRANIAN_MARKERS for t in ipa_tokens)
    vmap = IRANIAN_V if (style_ir and not style_cl) else CLASSICAL_V
    out = []
    for t in ipa_tokens:
        if t in COMMON:
            if COMMON[t] is not None:
                out.append(COMMON[t])
        elif t in vmap:
            out.append(vmap[t])
        else:
            return None      # exotic phone -> drop row
    return out

AR_NORM = str.maketrans({"ي":"ی","ك":"ک","ۀ":"ه","ة":"ه","أ":"ا","إ":"ا",
                         "ؤ":"و","ٔ":None,"ً":None,"ٌ":None,"ٍ":None,
                         "َ":None,"ُ":None,"ِ":None,"ّ":None,"ْ":None})

def ar_norm(s):
    return unicodedata.normalize("NFC", s).translate(AR_NORM)

TRANSLIT = {"a":"a","e":"e","i":"i","o":"o","u":"u","A":"â","b":"b","p":"p",
    "t":"t","d":"d","k":"k","g":"g","m":"m","n":"n","s":"s","z":"z","l":"l",
    "r":"r","f":"f","v":"v","h":"h","x":"kh","sh":"sh","zh":"zh","ch":"ch",
    "jh":"j","j":"y","q":"'","G":"q"}

def translit(phones):
    return "".join(TRANSLIT[p] for p in phones)

def load_freq():
    freq = {}
    with open(os.path.join(DATA, "fa_freq_50k.txt"), encoding="utf8") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 2 and parts[1].isdigit():
                freq[ar_norm(parts[0])] = int(parts[1])
    return freq

FA_BLOCKLIST = {"اوه","اه","هوم","اوم","خب","اووه","هان","ووه","اهم",
                "وو","هو","ها","هه","اووم","امم","ام"}

def load_wikipron():
    lex = {}   # script -> list of canonical phone tuples
    with open(os.path.join(DATA, "fas_arab_broad.tsv"), encoding="utf8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 2:
                continue
            word = ar_norm(parts[0])
            if "ـ" in word or word in FA_BLOCKLIST or len(word) < 2:
                continue
            phones = canon_row(parts[1].split(" "))
            if phones and 0 < len(phones) <= 14:
                lex.setdefault(word, [])
                if phones not in lex[word]:
                    lex[word].append(phones)
    return lex

# ---------------- curated verbs: (past stem phones, present stem phones,
#                  past script, present script, translit-past, gloss) -------
VERBS = [
    ("r a f t","r a v","رفت","رو","raft","go"),
    ("A m a d","A j","آمد","آی","âmad","come"),
    ("k a r d","k o n","کرد","کن","kard","do/make"),
    ("sh o d","sh a v","شد","شو","shod","become"),
    ("b u d","b A sh","بود","باش","bud","be"),
    ("d A sh t","d A r","داشت","دار","dâsht","have"),
    ("g o f t","g u","گفت","گو","goft","say"),
    ("d i d","b i n","دید","بین","did","see"),
    ("x A n d","x A n","خواند","خوان","khând","read/sing"),
    ("x o r d","x o r","خورد","خور","khord","eat/drink"),
    ("d A d","d e h","داد","ده","dâd","give"),
    ("g e r e f t","g i r","گرفت","گیر","gereft","take"),
    ("m A n d","m A n","ماند","مان","mând","stay/remain"),
    ("r e s i d","r e s","رسید","رس","resid","arrive"),
    ("n e sh a s t","n e sh i n","نشست","نشین","neshast","sit"),
    ("x A s t","x A h","خواست","خواه","khâst","want"),
    ("d A n e s t","d A n","دانست","دان","dânest","know"),
    ("z a d","z a n","زد","زن","zad","hit/strike"),
    ("b o r d","b a r","برد","بر","bord","carry/win"),
    ("A v a r d","A v a r","آورد","آور","âvard","bring"),
    ("g o z a sh t","g o z a r","گذشت","گذر","gozasht","pass"),
    ("s A x t","s A z","ساخت","ساز","sâkht","build"),
    ("r i x t","r i z","ریخت","ریز","rikht","pour/spill"),
    ("o f t A d","o f t","افتاد","افت","oftâd","fall"),
    ("m o r d","m i r","مرد","میر","mord","die"),
    ("x A b i d","x A b","خوابید","خواب","khâbid","sleep"),
    ("sh e k a s t","sh e k a n","شکست","شکن","shekast","break"),
    ("b a s t","b a n d","بست","بند","bast","close/bind"),
    ("j A f t","j A b","یافت","یاب","yâft","find"),
    ("sh e n i d","sh e n a v","شنید","شنو","shenid","hear"),
    ("p o r s i d","p o r s","پرسید","پرس","porsid","ask"),
    ("g e r i s t","g e r j","گریست","گری","gerist","weep"),
    ("t A x t","t A z","تاخت","تاز","tâkht","gallop/raid"),
    ("s u x t","s u z","سوخت","سوز","sukht","burn"),
    ("d u x t","d u z","دوخت","دوز","dukht","sew"),
]

PAST_END = [("a m","م","am","I"),("i","ی","i","you"),("","","","he/she"),
            ("i m","یم","im","we"),("i d","ید","id","you.pl"),
            ("a n d","ند","and","they")]
PRES_END = [("a m","م","am","I"),("i","ی","i","you"),("a d","د","ad","he/she"),
            ("i m","یم","im","we"),("i d","ید","id","you.pl"),
            ("a n d","ند","and","they")]

FUNCTION = [  # (phones, script, translit, gloss)
    ("o","و","o","and"),("v a","و","va","and"),("b e","به","be","to"),
    ("b A","با","bâ","with"),("b a r","بر","bar","upon"),
    ("d a r","در","dar","in"),("a z","از","az","from"),
    ("t A","تا","tâ","until"),("k e","که","ke","that/who"),
    ("ch e","چه","che","what"),("ch u n","چون","chun","like/since"),
    ("a g a r","اگر","agar","if"),("m a n","من","man","I"),
    ("t o","تو","to","you"),("u","او","u","he/she"),
    ("m A","ما","mâ","we"),("i n","این","in","this"),
    ("A n","آن","ân","that"),("h a r","هر","har","every"),
    ("h a m","هم","ham","also/together"),("h i ch","هیچ","hich","none"),
    ("n i s t","نیست","nist","is not"),("a s t","است","ast","is"),
    ("h a s t","هست","hast","there is"),("r A","را","râ","OBJ"),
    ("x o d","خود","khod","self"),("d e l","دل","del","heart"),
    ("jh A n","جان","jân","soul/dear"),("sh a b","شب","shab","night"),
    ("r u z","روز","ruz","day"),("A b","آب","âb","water"),
    ("b A d","باد","bâd","wind"),("m A h","ماه","mâh","moon"),
    ("x A k","خاک","khâk","earth/soil"),("d o q A","دعا","do'â","prayer"),
    ("t a n h A","تنها","tanhâ","alone"),("b A z","باز","bâz","again/open"),
    ("h a m e","همه","hame","all"),("d i g a r","دیگر","digar","other"),
    ("m a g a r","مگر","magar","unless/perhaps"),
    ("A n jh A","آنجا","ânjâ","there"),("i n jh A","اینجا","injâ","here"),
]

SUFFIXES = [  # (phones, script-attachment, translit, tag, gloss)
    ("e","","-e","ezafe","EZ"),
    ("i","ی","-i","indef","a certain/-ness"),
    ("a m","م","-am","cop1s","am"),
    ("i","ی","-i","cop2s","are(you)"),
    ("i m","یم","-im","cop1p","are(we)"),
    ("a n d","ند","-and","cop3p","are(they)"),
    ("h A","‌ها","-hâ","plural","PL"),
    ("A n","ان","-ân","plural_an","PL(anim)"),
    ("a m","م","-am","poss1s","my"),
    ("a t","ت","-at","poss2s","your"),
    ("a sh","ش","-ash","poss3s","his/her"),
    ("o","و","-o","clitic_and","and"),
]

NO_SUFFIX = {"هر","که","و","تا","از","به","با","هم","چه","اگر","یا","پس",
             "علی","in","بی","نه","ای","آی","ولی","اما","اگه","توی","برای"}

def build(min_freq=5, max_suffixed_bases=6000):
    freq = load_freq()
    wp = load_wikipron()
    entries = []   # dict: phones(tuple), script, translit, gloss?, freq, tag
    def add(phones, script, tr, gloss, fq, tag):
        entries.append({"ph": tuple(phones), "script": script, "tr": tr,
                        "gloss": gloss, "freq": fq, "tag": tag})
    seen_bases = []
    for word, prons in wp.items():
        fq = freq.get(word, 0)
        if fq < min_freq and len(word) > 1:
            continue
        for ph in prons:
            add(ph, word, translit(ph), None, max(fq, 1), "lex")
            seen_bases.append((ph, word, max(fq, 1)))
    # suffix expansion on frequent bases ending in a consonant (ezâfe etc.)
    from phonespace import is_vowel
    seen_bases.sort(key=lambda x: -x[2])
    for ph, word, fq in seen_bases[:max_suffixed_bases]:
        if word in NO_SUFFIX or len(ph) <= 2:
            continue
        for sph, sscript, str_, tag, sgloss in SUFFIXES:
            s = sph.split()
            if is_vowel(s[0]) and is_vowel(ph[-1]):
                continue          # avoid vowel hiatus; keep it simple
            add(list(ph) + s, word + sscript, translit(ph) + str_,
                None, max(fq // 3, 1), tag)
    for phones, script, tr, gloss in FUNCTION:
        add(phones.split(), script, tr, gloss,
            max(freq.get(ar_norm(script), 0), 500), "func")
    # verbs
    for past, pres, psc, prsc, ptr, gloss in VERBS:
        past, pres = past.split(), pres.split()
        for ends, script_forms, prefix_ph, prefix_sc, prefix_tr, mood in [
            (PAST_END, psc, [], "", "", "past"),
            (PAST_END, psc, ["m i"], "می‌", "mi-", "impf"),
            (PAST_END, psc, ["n a"], "ن", "na-", "neg.past"),
            (PRES_END, prsc, ["m i"], "می‌", "mi-", "pres"),
            (PRES_END, prsc, ["b e"], "ب", "be-", "subj"),
        ]:
            stem = past if "past" in mood or mood == "impf" else pres
            pre = (prefix_ph[0].split() if prefix_ph else [])
            for eph, esc, etr, pgl in ends:
                if mood != "past" and eph == "":
                    continue
                ph = pre + stem + (eph.split() if eph else [])
                sc = prefix_sc + script_forms + esc
                tr = prefix_tr + translit(stem) + ("-" + etr if etr else "")
                add(ph, sc, tr, f"{gloss}.{mood}.{pgl}", 60, "verb")
        # perfect participle rafte
        add(past + ["e"], psc + "ه", translit(past) + "-e",
            f"{gloss}.PTCP", 60, "verb")
    # dedupe identical (phones, script)
    out, seen = [], set()
    for e in entries:
        key = (e["ph"], e["script"])
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out

if __name__ == "__main__":
    lex = build()
    print("Persian lexicon size:", len(lex))
    import collections
    print(collections.Counter(e["tag"] for e in lex))
    for e in lex[:5]:
        print(e)
