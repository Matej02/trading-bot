---
tags: [vyzkum, f10, fm]
datum: 2026-10-29
---
# F10 – entry modely mentorů FM přesně podle PDF (minutová data)

Zadání uživatele: otestovat i Veselovského, Kimmela a Pátka a vůbec všechno, co je v [[FM materiály|FM PDF]]. Dokument z Wordu se už nepoužívá.
Plán předem v `F10_PLAN.md`, kód v `research_f10.py` a `research_f10_eval.py`, výstupy v `research_data/f10/`.

## Data
- MT5 M1: forex (EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD) a kovy od 2017, indexy (US100, US500, US30, DAX) od 2019.
- Vyšší TF jsou složené z M1. Simulace na M1 s náklady brokera.
- **Vývoj do 2021, OOS 2022–2026.** Varianta se vybírá jen na vývoji.

## Výsledky (OOS 2022–2026, vybraná varianta)
| Mentor a model | Trhy | OOS | Náhodné vstupy | Poznámka |
|---|---|---|---|---|
| [[FM Strategie – Michal Veselovský (day, ICT)\|Veselovský]]: bias → sweep Asie/PD pod NY open → MSS → FVG/0,382, TP1 Asie, TP2 PDH/PDL | 5 forex + XAU | **−0,24 R** (n 485) | −0,21 R | M5 i M1, obě varianty vstupu záporné |
| [[FM Strategie – Rafael Kimmel (day, indexy ICT)\|Kimmel]] model 1: dotek PDH/PDL → MSS M5, SL +25 % | US100, US500, US30, DAX | **−0,04 R** (n 186) | +0,02 R | model 2 (zóna + 2× BOS) −0,11 až −0,18 R |
| [[FM Strategie – Oliver Pátek (scalping NQ)\|Pátek]]: vyšší low → průraz M5 pivotu v trendu H4 | NQ, ES, GBPUSD, XAU | **−0,05 R** (n 2 868) | −0,06 R | NQ na vývoji +0,12 R, v OOS −0,01 R |
| [[FM Strategie – Jan Šrajer (day + swing)\|Šrajer DT]]: M15 zóna ve 4H zóně + sweep pivotu + discount, okna | 5 forex + XAU | **−0,29 R** (n 97) | −0,34 R | málo obchodů |
| [[FM Strategie – Petr Můčka (day, pravděpodobnosti)\|Můčka]]: Asie ≤ 35 pipů → sweep v Londýně/NY → shift M5 | 5 forex, XAU, NQ | **−0,23 R** (n 5 150) | −0,15 R | všech 8 variant −0,22 až −0,30 R |
| [[FM Strategie – Daniel Valchář (swing)\|Valchář]]: trend D1, H4 OB s POC (tick volume), sweep, TP předchozí high | 11 trhů | **−0,36 R** (n 306) | −0,01 R | horší než náhoda |
| [[FM Strategie – Sunita Hakimi (day, zlato)\|Hakimi]]: trend H4, Fibo 0,5–0,75 + zóna/FVG, RR ≥ 2,5 | 8 trhů | **−0,44 R** (n 153) | −0,14 R | vysoké RR, výhra jen 12 % |
| [[FM Strategie – Daniel Hvězda (swing)\|Hvězda]]: D1 zóna + hammer/engulfing, BE při 1R | 26 trhů | **−0,21 R** (n 187) | – | s trendem a SL +20 % −0,06 R (n 80) |

**Prahy (n ≥ 100, exp ≥ 0,15 R, PF ≥ 1,3, o 0,1 R nad náhodou) nesplnila žádná strategie** a žádná ani nemá kladný OOS.
Intradenní modely (Veselovský, Můčka, Šrajer DT) jsou na úrovni náhodných vstupů nebo pod nimi. Ztráta ~0,2 R odpovídá nákladům
na úzký stop (spread je velká část 6–20pipového SL, viz [[Náklady brokera]]).

## Bez nákladů (spread a swapy = 0, stejná pravidla)
| Mentor | OOS bez nákladů | Náhoda bez nákladů |
|---|---|---|
| Veselovský | −0,02 R (n 477) | −0,06 R |
| Kimmel M1 | −0,03 R (n 186) | +0,03 R |
| Pátek | +0,02 R (n 2 871) | +0,03 R |
| Šrajer DT | +0,04 R (n 137) | −0,03 R |
| Můčka | −0,03 R (n 3 147) | −0,02 R |
| Valchář | −0,38 R (n 409) | +0,01 R |
| Hakimi | −0,37 R (n 216) | −0,08 R |

Intradenní modely jsou bez nákladů na nule, stejně jako náhodné vstupy. Celá jejich ztráta s náklady je tedy spread.
Koncepty samy směr nepředpovídají.
Valchář a Hakimi jsou výrazně horší než náhoda i bez nákladů. Limit na hraně zóny se vyplní hlavně tehdy, když cena zónou projede
(nepříznivý výběr limitních vstupů), a malý SL za jednou svíčkou OB se snadno vyrazí.

## Závěr
Všechny strategie z FM PDF jsou teď otestované:
- S/D zóny na všech TF ([[F8 Strategie z FM PDF|F8]]);
- kombinace konceptů ([[F9 Kombinace FM konceptů|F9]]);
- entry modely všech 9 mentorů (F10).

Žádná nemá doloženou výhodu. Do simulátoru se nic dalšího nepřidává; experiment F9 v simulátoru dál sbírá live data.
