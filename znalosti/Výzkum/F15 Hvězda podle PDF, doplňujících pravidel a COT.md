---
tags: [vyzkum, f15, fm, cot]
datum: 2026-11-04
---
# F15 – Hvězda: PDF a obrázky jako zdroj, B4 jako dodatek, COT z CFTC

Prošel jsem celý text 27 PDF a všech **128 obrázků** [[FM obrázky – Daniel Hvězda (swing)|galerie]]. Z [[Doplňující pravidla k FM PDF|Wordu]] jsem bral jen B4 jako dodatek.
Uživatel 2026-11-04 schválil stažení COT. **Data CFTC** (Legacy, futures only, 2009–2026, 18 ročních souborů, 220 269 záznamů) jsou v
`research_data/cot/`. Modul `research_f15_cot.py` počítá COT index 26 týdnů s prahy 20/80 jako na Hvězdových grafech (obr. 118–121). Report je
použitelný až od soboty po vydání (bez pohledu do budoucnosti). U USDJPY, USDCAD a USDCHF je znaménko otočené.
Kód: `research_f15_hve.py`, `research_f15_eval.py`, plán `F15_PLAN.md`, výstupy `research_data/f15/`.

## COT samotný ([[COT]])
Výnos po extrému (13 trhů, v σ, vývoj do 2021 | OOS 2022–26):

| Skupina na extrému | 4 týdny | 13 týdnů |
|---|---|---|
| commercials ve směru (≥ 80 long / ≤ 20 short) | +0,03 \| +0,05 | +0,05 \| +0,15 |
| non-commercials (fondy) proti | −0,04 \| −0,03 | −0,06 \| −0,13 |
| retail proti | +0,03 \| +0,01 | −0,01 \| +0,04 |

Commercials mají slabý, ale v obou obdobích kladný směr (týdny se překrývají, takže to není samostatný signál).
Při ladění jsem našel a opravil chybu: datum v mikrosekundách dávalo pro celou historii poslední report (pohled do budoucnosti).

## Pravidla v testu
- **Zóna FM** (F8): příchod, base, odchod ≥ 1,5 ATR. Base max 3 (B4: „1–3 kvalitní“) nebo 6. Proximal přes těla base, distal knot, aktivace po BOS.
  Jen ve směru trendu (2 vyšší high i low).
- **Týdenní příjem:** W1 zóna, vstup na D1. **Denní příjem:** D1 zóna, vstup na H4 [PDF Denní a týdenní strategie].
- **Varianty:**
  - zóna nižšího TF uvnitř zóny vyššího („denní level v týdenním“, obr. 14–26);
  - **level nad levelem** = SL pod 2. zónou (obr. 37–64);
  - limit na proximal nebo hammer/engulfing (obr. 2–12);
  - COT: vypnutý / commercials ve směru (> 50) / extrém (≥ 80 nebo ≤ 20 v posledních 4 reportech).
- SL pod distal. TP nejbližší protější zóna (2–6 R). BE při 1R. Nejdéle 30 / 10 dní.

## Výsledky (s náklady, vývoj do 2021, OOS 2022–26)
- 96 variant, 1 450 obchodů. **Hvězda obchoduje velmi málo:** ~60 obchodů na variantu za 16 let na 13 trzích.
- **Vybraná** `denní příjem, base ≤ 3, H4 zóna v D1 zóně, level nad levelem, limit, bez COT`:
  - vývoj **+0,22 R** (n 44), OOS **−0,17 R** (n 13);
  - náhoda vývoj +0,03 R, OOS −0,15 R.
- **Podle parametrů:**
  - zóna v zóně vyššího TF (vývoj +0,05 / OOS −0,04 R) a level nad levelem (+0,03 / −0,07 R) jsou lepší než bez nich (−0,18 / −0,35 a −0,09 / −0,32 R);
  - týdenní příjem: vývoj −0,32 R (n 54), OOS +0,33 R (n 39) – nekonzistentní;
  - **COT filtr nepomohl:** bez COT −0,07 / −0,27 R, „směr“ −0,06 / −0,18 R, „extrém“ −0,03 / −0,38 R.

## Závěr
- **Bez doložené výhody.**
- Hvězdovy konfluence (D v W, level nad levelem) zlepšují proti holé zóně, ale samy jsou ztrátové nebo na nule a vzorky jsou malé.
- COT má slabý vlastní směr (commercials), jako filtr zón ho to ale nezlepšilo.
- Potvrzuje [[F8 Strategie z FM PDF|F8]] a [[F11 Mentoři FM znovu a podrobně|F11]] (limit do zóny je ztrátový).
