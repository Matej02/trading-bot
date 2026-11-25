---
tags: [vyzkum, f91, prop, plan]
datum: 2026-11-25
---
# F91 Pravidla prop firem v měřítku

Zadání uživatele (2026-11-25): „Ano, začni bodem 1 a pak 2.“ Bod 2 = porovnat pravidla dalších firem stejným výpočtem jako [[F89 Porovnání zkoušek FTMO 1 krok a 2 kroky|F89]]. Bot ani runner se nemění.

## Pravidla z oficiálních stránek (čteno 25. 11. 2026, účet 100 000)
| | FTMO 2 kroky | The5ers High Stakes Classic | Fintokei ProTrader | Fintokei ProTrader Swing | FundedNext Stellar 2 kroky |
|---|---|---|---|---|---|
| Cíl | +10 %, +5 % | **+8 %, +5 %** (tarif New: 10 % a 5 %) | **+8 %, +6 %** | +8 %, +6 % | +8 %, +5 % |
| Denní limit | equity < zůstatek o půlnoci − 5 % počátečního | equity < **vyšší z (zůstatek, equity) na konci předchozího dne** − 5 % z ní; jiná stránka uvádí **3 %** | equity < **equity o půlnoci UTC** − 5 % z ní | equity < **zůstatek o půlnoci UTC** − 5 % z něj | 5 % počátečního, výpočet mezi stránkami nejednotný |
| Celkový limit | 90 % statický | 90 % statický | 90 % statický | 90 % statický | 90 % (stránky si odporují: statický / posuvný) |
| Min. dní | 4 dny se vstupem | 3 **ziskové dny** (≥ 0,5 % za den) | 3 dny s otevřeným obchodem | 3 | 5 |
| Časový limit | ne | ne | ne | ne | ne |
| Jiné | | zákaz obchodů 2 min kolem důležitých zpráv; neaktivita 30 dní ve zkoušce | **ztráta otevřených obchodů ≥ 3 % = varování, pak omezení** (páka, denní ztráta −1 %); neaktivita 30 dní na financovaném účtu | jako ProTrader, navíc bez swapů (nákup od 15. 7. 2026) | **EA na účtech od 50 000 nepovolené** |
| Cena 100k | 540 € (teď 432 €), vratná | 179 $ (vrácení nejasné) | 549 $ (vrácení neuvedeno) | 679 $ (vrácení neuvedeno) | 549,99 $, vratná |
| US indexy | ano | ano (indexy, 1:100) | „CFD indices“, konkrétní US500/US100 neuvedeny | stejně | neuvedeno |

Zdroje:
- FTMO: [2 kroky](https://ftmo.com/en/2-step-challenge/), [pravidla](https://ftmo.com/en/trading-objectives/).
- The5ers: [denní limit High Stakes](https://the5ers.com/faqs/what-is-the-drawdown-rule-for-high-stakes/), [2 kroky](https://the5ers.com/faqs/2-step-plan-rules-specifications/), [High Stakes](https://the5ers.com/high-stakes/), [obecná pravidla](https://the5ers.com/faqs/what-are-the-general-rules-for-the-high-stakes-program/).
- Fintokei: [ProTrader](https://support.fintokei.com/en/articles/6538822-how-does-the-protrader-challenge-work-what-are-the-rules), [výpočet limitů](https://support.fintokei.com/en/articles/6538826-how-are-the-daily-loss-limit-and-maximum-loss-limit-calculated), [riziko otevřených obchodů](https://support.fintokei.com/en/articles/11315976-what-is-the-maximum-risk-on-open-trades), [Swing](https://support.fintokei.com/en/articles/12058210-what-is-the-difference-between-protrader-and-protrader-swing), [programy](https://www.fintokei.com/programs/).
- FundedNext: [Stellar 2 kroky](https://help.fundednext.com/en/articles/17255124-stellar-2-step-challenge), [produkt](https://fundednext.com/cfds/stellar-2-step), [limity](https://help.fundednext.com/en/articles/9941519-daily-loss-limit-vs-maximum-loss-limit).

## Plán (zapsán PŘED výpočtem)
**Tvrdé podmínky (bez nich se firma nepočítá):** vlastní automatické obchodování na účtu 100k, držení přes noc a víkend, bez časového limitu.
- **FundedNext vypadá:** EA na účtech od 50 000 nepovolené (nápověda FundedNext). Dřívější výhrada: víkendové držení v roce 2026 vypnuli a zase zapnuli.

**Obchody a simulace:** základ měřítka F33 se stopem + RSI(2) ([[F87 Měřítko s F33 se stopem jako v runneru|F87]]), starty každý měsíc 2003–2023, nejdéle 36 měsíců, nejhorší equity dne = všechny pozice na svém low zároveň, riziko 0,5–3,0 % po 0,25.

**Varianty:**
1. FTMO 2 kroky (základ, musí se shodovat s F89).
2. The5ers Classic, denní 5 %: cíl 8 % a 5 %, denní hranice = 0,95 × vyšší z (zůstatek, equity) na konci předchozího dne, 3 ziskové dny (min(zůstatek, equity) na konci dne − zůstatek předchozího dne ≥ 0,5 %).
3. The5ers Classic, denní 3 % (stránky si odporují, proto obojí): stejné, hranice 0,97 ×.
4. Fintokei ProTrader: cíl 8 % a 6 %, denní hranice = 0,95 × equity na konci předchozího dne, 3 dny s otevřenou pozicí.
5. Fintokei Swing: stejné, denní hranice = 0,95 × zůstatek na konci předchozího dne.

U Fintokei se navíc počítá **varování**: den, kdy otevřené obchody dohromady (na svém low) ztrácejí ≥ 3 % počátečního kapitálu.

**Provozní riziko:**
- každá varianta: nejvyšší r s propady ≤ 10 % na celém období;
- u Fintokei navíc: varování nanejvýš v 10 % zkoušek. Po varování přijdou omezení (páka, denní ztráta −1 %), která by strategie zastavila.

**Rozhodnutí:** první volba se změní z FTMO na jinou firmu, jen když platí vše:
1. P24 při provozním riziku je aspoň o **10 p. b. vyšší** než u FTMO (17 %);
2. při stejném riziku propadlo ≤ 10 % ve vývoji (starty 2003–2014) i v kontrole (2015–2023);
3. u The5ers musí bod 1 a 2 platit pro denní limit 5 % i 3 % (nevíme, který platí).

Jinak FTMO zůstává první volbou a ostatní se zapíší jako popis.

**Popis (nerozhoduje):** P12, P36, medián, poplatek / P36, podíl zkoušek s mezerou > 30 dní bez obchodu, kontrola r* vybraného na vývoji.

**Co se nemodeluje:**
- Swing u Fintokei je bez swapů. Strategie by tam vyšly o něco lépe, výpočet je tedy pro Fintokei Swing pesimistický.
- Zákaz obchodů 2 min kolem zpráv u The5ers: runner vstupuje na otevření a F31 zavírá 5 min před FOMC, takže nevadí.

Skript `scratch/f91_firmy.py`, výstup `research_data/prop/f91_souhrn.txt`.
