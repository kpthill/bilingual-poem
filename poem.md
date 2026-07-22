# Tanah, Tanah, Rumah / تنها، تنها، رو ماه (tanhâ, tanhâ, ru mâh)

*A phonetically dual-language poem: one phoneme stream, two readings.*

Read aloud in the compromise accent, every line below is simultaneously an Indonesian line (left gloss) and a Persian line (right gloss), with different word boundaries.

## The poem

### 1.

**IPA (shared stream):** `d o (ʔ) aː dʒ aː d i d e s a b u r a m`

| | text | literal English |
|---|---|---|
| **Indonesian** | *doa jadi desa buram* | prayer becomes a blurred village |
| **Persian** | دعا جا دیده، صبورم — *do'â jâ dide, sabur-am* | the prayer has found its place; I am patient |

### 2.

**IPA (shared stream):** `h a r i d e s a d aː n a j a m`

| | text | literal English |
|---|---|---|
| **Indonesian** | *hari desa dan ayam* | the village day and the chickens |
| **Persian** | هر عیدِ صدا نی‌ام — *har 'id-e sadâ nay-am* | at every feast of sound, I am the reed-flute |

### 3.

**IPA (shared stream):** `h aː l i b u d a s a r r u m a h`

| | text | literal English |
|---|---|---|
| **Indonesian** | *hal ibu dasar rumah* | mother's matter is the foundation of the house |
| **Persian** | حالی بود، اثر رو مه — *hâli bud, 'asar ru mah* | there was a feeling — a trace upon the moon |

### 4.

**IPA (shared stream):** `t a n aː h i b u d a l a m t i r a m`

| | text | literal English |
|---|---|---|
| **Indonesian** | *tanah ibu dalam tiram* | mother's land inside an oyster |
| **Persian** | تن آهی بود، علم، تیرم — *tan 'âhi bud, 'alam, tir-am* | the body was a sigh; O banner, I am the arrow |

### 5.

**IPA (shared stream):** `t aː d i d a l a m b u d i`

| | text | literal English |
|---|---|---|
| **Indonesian** | *tadi dalam budi* | a moment ago, within kindness |
| **Persian** | تا دید، علم بودی — *tâ did, 'alam budi* | the moment he looked, you were the banner |

### 6.

**IPA (shared stream):** `k i t aː ʔ a d a m a l a m r a h i m`

| | text | literal English |
|---|---|---|
| **Indonesian** | *kita ada malam rahim* | we are here; the night is a womb |
| **Persian** | که تا عدم، علم، رهیم — *ki tâ 'adam, 'alam, rah-im* | for until nothingness, banner aloft, we are the road |

### 7.

**IPA (shared stream):** `r o̞ s a d aː n a b u d i r u m a h`

| | text | literal English |
|---|---|---|
| **Indonesian** | *rusa dan abu di rumah* | the deer and the ash are in the house |
| **Persian** | رو، صدا نبودی رو مه — *ro, sadâ nabudi ru mah* | go — you were not even a sound upon the moon |

### 8.

**IPA (shared stream):** `r u m a͡h s u d a͡h r aː h i m`

| | text | literal English |
|---|---|---|
| **Indonesian** | *rumah sudah rahim* | the house has already become a womb |
| **Persian** | روم حسود، هر آهیم — *rum hasud, har 'âh-im* | Rome is envious; we are every sigh |

### 9.

**IPA (shared stream):** `t a n a͡h t aː d i d a n k a b u t`

| | text | literal English |
|---|---|---|
| **Indonesian** | *tanah tadi dan kabut* | the land from before, and the fog |
| **Persian** | تنها تا دید عنکبوت — *tanhâ tâ did 'ankabut* | alone, until the spider saw |

### 10.

**IPA (shared stream):** `t a n a͡h t a n a͡h r u m aː h`

| | text | literal English |
|---|---|---|
| **Indonesian** | *tanah tanah rumah* | land, land, home |
| **Persian** | تنها، تنها، رو ماه — *tanhâ, tanhâ, ru mâh* | alone, alone, upon the moon |

## Per-line accent-cost annotations

Cost table: see `src/phonespace.py`. Poem totals: **21.0 cost / 71 syllables = 0.30 per syllable**.

| # | syll | cost | compromises |
|---|---|---|---|
| 1 | 8 | 3.0 | fa /q/ deleted (cost 1); a~A (cost 1.0); a~A (cost 1.0) |
| 2 | 7 | 1.0 | a~A (cost 1.0) |
| 3 | 7 | 1.0 | a~A (cost 1.0) |
| 4 | 8 | 1.0 | a~A (cost 1.0) |
| 5 | 6 | 1.0 | a~A (cost 1.0) |
| 6 | 8 | 1.0 | a~A (cost 1.0) |
| 7 | 8 | 2.0 | u~o (cost 1.0); a~A (cost 1.0) |
| 8 | 6 | 3.0 | metathesis a+h ~ h+a (cost 1.0); metathesis a+h ~ h+a (cost 1.0); a~A (cost 1.0) |
| 9 | 7 | 3.0 | metathesis a+h ~ h+A (cost 1.0+1); a~A (cost 1.0) |
| 10 | 6 | 5.0 | metathesis a+h ~ h+A (cost 1.0+1); metathesis a+h ~ h+A (cost 1.0+1); a~A (cost 1.0) |

## Blind recoverability audit

Independent auditors were shown ONLY the IPA stream (no intended readings) and asked what they hear.

| # | Indonesian ear heard (score/5) | Persian ear heard (score/5) |
|---|---|---|
| 1 | doa jadi desa buram (3) | doâ [dʒâ?] dide saburam (2) |
| 2 | hari desa dan ayam (4) | haride sadâ … na(y)am (2) |
| 3 | hali(bu) dasar rumah (?) (2) | hâli bud[a] sar … (2) |
| 4 | tanah ibu dalam tiram (4) | tanâhi budam alam tir(e)am (3) |
| 5 | tadi dalam budi (4) | tâ did … alam budi (2) |
| 6 | kita ada malam rahim (4) | ki tâ adam alam rahim (1) |
| 7 | rusa dana budi rumah (3) | ro sadâ nabudi ru mâh (2) |
| 8 | rumah sudah rahim (4) | ru mâh sude râhim (2) |
| 9 | tanah tadi dan kabut (5) | tanah tâ didan-e kabut (2) |
| 10 | tanah tanah rumah (5) | tanhâ tanhâ ru mâh (3) |
