---
tags: [vyzkum, f9, fm]
datum: 2026-10-29
---
# F9 – kombinace FM konceptů (koncepty pevné, strategie se skládají)

Zadání uživatele: koncepty z [[FM materiály|FM PDF]] si nechat, měnit jen strategie. Kombinovat popsané věci, otestovat a nasadit na web k live testu.
Plán předem: `F9_PLAN.md`. Skripty: `research_f9.py`, `research_f9_eval.py`. Výstupy: `research_data/f9/`.

## Stavební bloky
**Spouštěče** (koncepty):
- [[SFP – sweep likvidity|sweep PDH/PDL]] a sweep Asie ([[Killzones a session]]);
- [[MSS a displacement|MSS po sweepu]];
- retest 50 % [[FVG]];
- retest [[Order block|OB]] po BOS;
- [[Supply a demand zóny|S/D zóna H4]] s potvrzovací svíčkou ([[Svíčkové formace|Hvězda]]);
- průraz pivotu (Pátek);
- [[Support a rezistence|balanční level]] (retest proraženého H4 pivotu).

**Filtry:**
- trend D1 a trend H4 ([[Market structure]]);
- EMA20 D1;
- [[Daily bias]] Veselovského a Můčky;
- [[Premium a discount|discount/premium]] 10denního range;
- killzone;
- [[Daily Open a Power of 3|pod/nad NY open]];
- uvnitř H4 zóny.

**Kombinace:** 8 spouštěčů × (0–2 filtry z 9) × TP 1,5/2/3R = **1 104 kombinací**, zvlášť na H1 a na H4 základu (2 208 celkem).
28 trhů s náklady brokera, 2010–2026. Výběr 2010–17, validace 2018–21, holdout 2022–26.

## Výsledek
| | H1 základ | H4 základ |
|---|---|---|
| Spouštěče samotné (TP 2R) | −0,07 až −0,21 R ve všech obdobích | 0,00 až −0,17 R |
| Kladných kombinací na vývoji (n ≥ 100) | 6 z 1 053 | 47 z 858 |
| Prošlo výběrem (exp > 0, t > 2) | **0** (náhodou by se čekalo ~25) | **0** |
| Kladných i ve validaci | 0 | 0 |

Nejlepší H4 kombinace na vývoji:
- **sweep → MSS + trend D1 + trend H4, TP 3R:** 2010–17 +0,05 R (t 1,0), 2018–21 −0,06 R, 2022–26 −0,03 R (n 604).
- **průraz pivotu + trend H4 + daily bias M, TP 3R:** +0,03 R, −0,07 R, −0,05 R (n 1 867).
- **S/D zóna H4 + potvrzení + trend D1 + H4, TP 3R:** −0,07 R, 0,00 R, −0,08 R (n 323).

Žádná kombinace nemá výhodu ani na datech, na kterých se vybírala. Kombinování neztrátových prvků dává jen šum kolem nákladů
(spouštěče jsou samy o sobě o −0,1 až −0,2 R horší než náhoda, to je zhruba cena spreadu; viz [[Náklady brokera]]).

## Live experiment v simulátoru (na přání uživatele)
Tři nejlepší kombinace (jedna na každý typ spouštěče) jsou v [[Simulátor|simulátoru]] jako systémy `fm_mss_h4`, `fm_pruraz_h4` a `fm_zona_h4`.
- Označení **„experiment F9 – NEOVĚŘENO“**, registr `unvalidated`.
- Logika je převedená 1:1 z Pythonu (`simulator/lib/fm.ts`). Kontrola `scripts/compare-fm.ts`: **119/120 signálů shodných**, rozdíl je jedna chybějící hodina dat u zlata.
- Signál na zavření H4 bloku (z H1, den 17:00 NY), SL podle konceptu, **TP 3R**, nejdéle 8 dní.
- Živě na 21 trzích: forex, XAU, XAG, ropa, BTC a ETH. **Akciové indexy ne**, protože Yahoo dává pro ^GSPC a podobné jen hodiny burzy a H4 bloky by neseděly s testem.
- Očekávání podle holdoutu je kolem −0,03 až −0,08 R na obchod. Live slouží ke sběru dat a kontrole, ne jako ověřená strategie.

## Co z toho plyne
- Koncepty FM (sweep, MSS, FVG, OB, S/D, pivoty, bias, killzones, discount) nedávají výhodu samy ani v kombinacích, na H1 ani na H4.
- Do vaultu zapsáno: [[Co nefunguje]] a jednotlivé koncepty (sekce Otestováno).
