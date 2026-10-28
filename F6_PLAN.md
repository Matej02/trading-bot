# F6 – hledání strategie, která funguje (plán a průběh)

Cíl uživatele (2026-10-28): co nejvyšší úspěšnost, nebo dobře rozložený poměr výher a proher
(1 obchod +10 000 a 3× −500 je v pořádku), s rozumným risk managementem a agenty.

Co víme z F1–F5: na 1h a menších timeframech u tohoto brokera nic nefunguje – spread je velká část SL
a samotné signály (S/R, SMC, volume profile, fakeouty) nemají výhodu ani bez nákladů. Jediné kladné:
denní průraz s týdenním trendem (F2), ale hlavně v letech 2024–26.

## Úkoly
1. **Data** – denní historie co nejdelší pro všech 39 trhů (Yahoo, desítky let) → `research_data/f6_*_1d.pkl`.
   Náklady vždy z brokera (spread v dané hodině přepočtený na cenu Yahoo, swapy).
2. **Rodiny strategií s doloženou výhodou** (denní, drží dny až týdny):
   - MR1 RSI(2) pullback v trendu (Connors) – vysoká úspěšnost, výstup nad SMA5
   - MR2 IBS – zavření u minima dne v trendu, výstup další den / při silném zavření
   - MR3 „double seven“ – 7denní minimum v trendu, výstup na 7denním maximu
   - TF1 Donchian průraz s trailing stopem (želvy) – nízká úspěšnost, velké výhry
   - TF2 průraz F2 s trailing stopem místo pevného TP
   - SE1 turn-of-month (indexy) – sezónnost
   Vstup vždy na otevření dalšího dne po signálu (realisticky, bot vidí zavření až po něm).
3. **Ověření** – výběr do 2018, kontrola 2019–2023, holdout 2024+; skupiny trhů předem
   (indexy / forex / komodity / krypto); Bonferroni podle počtu testovaných kombinací.
4. **Robustnost** – sousední parametry, náklady ×1,5, výsledky po letech, Monte Carlo drawdownu.
5. **Portfolio a risk management** – kombinace prošlých strategií, riziko na obchod, korelace,
   max. drawdown, úspěšnost a poměr výhra/prohra celého portfolia.
6. **Nasazení** – prošlé strategie do simulátoru (TS, kontrola shody s Pythonem), registr pro Statistika,
   Risk agent podle výsledků portfolia.

## Průběh
- **Úkol 1 hotovo** – Yahoo denní data: indexy od 1970–93, forex od 2003, komodity od 2000, krypto od 2014 (`research_f6_data.py`).
- **Úkoly 2–3 kolo 1** (`research_f6.py`, výstup `research_data/f6_vystup.txt`): 6 rodin × 4 skupiny, nic neprošlo všemi
  třemi obdobími. Mean reversion na indexech: úspěšnost 64–68 %, výběr t 3,8, kontrola ~0. Trend-following denní:
  forex ztrátový, jinde nekonzistentní. Turn-of-month indexy: slabě kladný všude.
- **Kolo 2** (`research_f6b.py`, kandidáti vybraní jen z dat do 2018: long-only, vstup na zavření):
  K1 RSI(2) long indexy – kladný ve všech obdobích (výběr +0,077 R t 3,6 / kontrola +0,037 t 0,6 / holdout +0,084 t 1,9),
  úspěšnost 67–72 %, formálně neprošel (kontrola). US indexy (silnější už ve výběru): 2019+ win 71 %, PF 1,9, t 2,8.
  K2 double seven a K3 turn-of-month neprošly.
- **Úkol 5**: portfolio průraz F2 + RSI(2) US při 0,25 % riziku: od 2019 +2,6 %/rok, max DD 7,3 %, win 48 %;
  od 2024 +7,2 %/rok, DD 1,7 %, win 58 %. RSI(2) má malé drawdowny → snese vyšší riziko na obchod.
- **Úkol 6**: RSI(2) US přidána do simulátoru jako kandidát `mr_rsi2_d1` (výstup nad SMA5, bez TP, max 10 dní,
  stop 3 ATR), shoda TS/Python 273/273 signálů; v registru „neověřeno“ → obchoduje v učícím režimu.

## Další kroky
- Nechat RSI(2) a průraz běžet živě (forward test), vyhodnotit po ~30 obchodech.
- Hledat další nezávislé zdroje výhody pro portfolio (jiné třídy trhů / jiné horizonty), vždy stejným postupem.
