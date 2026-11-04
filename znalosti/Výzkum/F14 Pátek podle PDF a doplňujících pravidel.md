---
tags: [vyzkum, f14, fm]
datum: 2026-11-04
---
# F14 – Pátek: PDF a obrázky jako zdroj, doplňující pravidla (B3) jako dodatek

Prošel jsem:
- celý text 25 PDF;
- všech **80 obrázků** [[FM obrázky – Oliver Pátek (scalping)|galerie]];
- B3 z [[Doplňující pravidla k FM PDF|Wordu]] jen jako dodatek.

Plán předem je v `F14_PLAN.md`, kód v `research_f14_pat.py` a `research_f14_eval.py`, výstupy v `research_data/f14/`.

## Pravidla v testu
- **Trend H4** z pivotů (2 vyšší high + 2 vyšší low).
- **H4 S/R zóna** = ≥ 2 pivoty (high i low, role reversal) do 0,25 ATR H4 [PDF S/R H4/H1, obr 27–39; B3 „po 2 dotycích“].
- **Model A** (ve směru H4, Entry model obr 71–74):
  1. odmítnutí v H4 zóně;
  2. nižší high / vyšší low z pivotů M5/M15 (N 3);
  3. close za posledním pivotem → vstup trhem;
  4. SL za LH/HL + 10 ticků;
  5. TP 2R / H1 pivot / protější H4 zóna (RR 2–5).
- **Model B** (proti H4, pullback, obr 75–80): HL/LH a průraz pivotu proti H4. TP = H4 zóna „z levé strany“, SL pod svíčkou před průrazem.
- **Session:** Londýn a NY stock (Praha 9–12 a 15:30–18, nebo celé). Zavřít do 22:00, bez BE.
- **Trhy:** NAS100, GBPUSD, XAUUSD (jeho). Mimo test SPX500, US30, DAX.
- Trendline a patterny (trojúhelník, vlajka) kódem nejsou. Nahrazuje je LH/HL + průraz pivotu.

## Výsledky (s náklady, vývoj do 2021, OOS 2022–26)
- 16 variant, 16 861 obchodů.
- **Vybraná na vývoji** `A, M15, celé session, TP protější H4 zóna`:
  - vývoj **+0,27 R** (n 50), OOS **+0,12 R** (n 59);
  - náhoda se stejným SL/TP, časem a směrem: vývoj −0,26 R, **OOS +0,21 R**. V OOS je tedy strategie horší než náhoda.
  - Mimo test: DAX OOS +0,33 R (19), SPX500 −0,01 R (26), US30 −0,65 R (21).
  - Bez nákladů OOS +0,17 R.
- **Ostatní varianty:**
  - model A v průměru vývoj −0,08 R, OOS −0,07 R;
  - model B (pullback) −0,14 / −0,12 R;
  - TP 2R −0,07 R ve všech obdobích.
- **Vrstvy:**
  - odmítnutí v H4 zóně zlepšuje (bez něj vývoj +0,05 R, OOS −0,01 R);
  - LH/HL přidá málo;
  - shoda s D1 zúží na 16 a 20 obchodů.

![[F14 Pátek – ukázky obchodů NAS100 (OOS).png]]

## Závěr
**Bez doložené výhody.**
- Jediná kladná varianta stojí na ~50 obchodech za 7 let a v OOS ji porazí náhodné vstupy.
- Základní model (2R) je trvale mírně ztrátový, stejně jako v [[F10 Entry modely mentorů FM|F10]] a [[F11 Mentoři FM znovu a podrobně|F11]].
- Užitečné zjištění: **odmítnutí v H4 S/R zóně** filtr zlepšuje.
