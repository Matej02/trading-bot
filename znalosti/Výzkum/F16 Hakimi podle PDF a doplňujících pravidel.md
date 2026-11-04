---
tags: [vyzkum, f16, fm]
datum: 2026-11-04
---
# F16 – Hakimi: PDF a obrázky jako zdroj, B5 jako dodatek

Prošel jsem celý text 29 PDF a všech **125 obrázků** [[FM obrázky – Sunita Hakimi (day)|galerie]]. Z [[Doplňující pravidla k FM PDF|Wordu]] jsem bral jen B5.
Plán předem je v `F16_PLAN.md`, kód v `research_f16_hak.py` a `research_f16_eval.py`, výstupy v `research_data/f16/`.

## Pravidla v testu
- Trend H4 (2 vyšší high + low).
- [[Elliottovy vlny]] mechanicky ZigZagem na 15m (zavírání, otočka 2 ATR):
  - vlna 1 = noha ve směru H4 s BOS, vlna 2 nesmí za začátek vlny 1;
  - varianta vlna 4: vlna 3 delší než 1 a vlna 4 nesmí do vlny 1.
- **Zóna vstupu:** Fibo vlny 0,618–0,75 [obr 37–44, 119–121], navíc 15m S/D zóna nebo FVG z vlny.
- **Vstup:** limit na hraně pásma, nebo 15m svíčka zavře zpět nad 0,618 (reakce).
- **SL:** pod zónou / 0,75, nebo za začátkem vlny.
- **TP:** high vlny (LOC likvidita), nebo extenze 1,618.
- RR ≥ 2,5, bez BE, konec dne 22:00. Bez dní FOMC a NFP. Bez session filtru (B5).
- Výběr na XAU+XAG, ověření na EURUSD, GBPUSD a NAS100.

## Výsledky (s náklady, vývoj do 2021, OOS 2022–26)
- 48 variant.
- **Vybraná na vývoji** `vlna 4, FVG v pásmu, vstup po potvrzení, SL pod zónou, TP LOC`:
  - vývoj **+0,04 R** (n 40), OOS **+0,07 R** (n 45);
  - náhoda −0,27 / −0,07 R;
  - bez nákladů +0,22 / +0,19 R.
- **Mimo výběr ztrácí:** EURUSD vývoj −0,35 R / OOS −0,22 R, GBPUSD −0,63 / −0,14 R, NAS100 +0,36 / −0,21 R.
- **Podle parametrů:**
  - **limit do pásma −0,34 / −0,23 R**, potvrzení −0,12 / −0,05 R;
  - zóna nebo FVG navíc k Fibo nic nemění;
  - SL za začátkem vlny je lepší než těsný.

## Závěr
- **Bez doložené výhody.**
- Potvrzuje [[F10 Entry modely mentorů FM|F10]] a [[F11 Mentoři FM znovu a podrobně|F11]]: limit do Fibo/zóny je ztrátový, vstup po reakci je kolem nuly.
- Většinu ztráty dělají náklady (těsný SL na zlatě).
- Elliott je nahrazený ZigZagem; ruční počítání vln (víc scénářů najednou) kódem převést nejde.
