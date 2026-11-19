---
tags: [vyzkum, f55, f56, f57, kalendar, indexy, ibs]
datum: 2026-11-19
---
# F55 až F57 Začátek měsíce, IBS a dny zpráv

Zadání uživatele (2026-11-19): „Pokračuj do té doby, dokud nenajdeš něco, co je pozitivní a co bude profitabilní.“

**Proč tyto tři:** na US indexech výhoda typu RSI(2) funguje ([[F42 RSI(2) přísná prověrka|F42]]), jinde ne (F49, F53, F54). Hledá se proto dál hlavně na US indexech, a to jevy dobře popsané v literatuře, které ve vaultu ještě nejsou:
- **F55 Přelom měsíce (turn-of-the-month):** většina růstu akcií připadá na poslední den měsíce a první 3 dny dalšího (Lakonishok a Smidt 1988, McConnell a Xu 2008). Jiné než [[F33 Rebalancování na konci měsíce|F33]] (ta obchoduje dny L−2 až L podle výkonu akcie/dluhopisy).
- **F56 IBS (síla zavření v denním rozpětí):** zavření u minima dne nad SMA200 → krátký návrat. Stejná rodina jako RSI(2), ale jiný spouštěč.
- **F57 Prémie v den zpráv (CPI, NFP):** akcie vydělávají hlavně v dny makro zpráv (Savor a Wilson 2013). Jiné než [[F27 Pokračování po zprávách (NFP, CPI)|F27]] (to byl směr prvních 15 minut).

**Pozor na lovení náhody:** testuje se série nápadů, dokud něco neprojde. Proto se laťka nesnižuje. Co projde, jde **jen do simulátoru** na sledování dopředu, do MT5 bota až po sledování a se souhlasem ([[Cesta k prop účtu]]).

## Plán (zapsán PŘED výpočtem)
**Společné:**
- Trhy US: SPX500, NAS100, US30. Jiné trhy: DAX, FTSE, CAC (Yahoo).
- Vývoj Yahoo do 2018, kontrola Yahoo 2019–2026, druhý zdroj H1 brokera → denní 2019–2026.
- Náklady: půl spreadu brokera na vstupu i výstupu, swap long za noci (středa 3×).
- Hodnotí se po dnech vstupu (průměr trhů). Převis = signál − srovnání, Welch t.

**F55 Přelom měsíce:**
- Long na otevření posledního obchodního dne měsíce, ven na zavření 3. obchodního dne dalšího měsíce (4 dny). Bez stopu.
- R = výsledek / ATR20.
- Srovnání: stejné 4denní okno (otevření dne d → zavření d+3) ve všech ostatních dnech.
- Vývoj od 1990.

**F56 IBS:**
- Signál na zavření: IBS = (C − L) / (H − L) < 0,2 a zavření > SMA200.
- Vstup na otevření dalšího dne. Ven na prvním zavření nad maximem předchozího dne, stop 3 ATR20, nejdéle 5 dní. Na trhu jen 1 pozice.
- R = výsledek / 3 ATR.
- Srovnání: stejné vstupy a výstupy ve všech dnech nad SMA200.
- Vývoj od 1990. Popis (nerozhoduje): kolik vstupů IBS se kryje s otevřeným obchodem RSI(2).

**F57 Den zpráv:**
- Long od zavření předchozího dne do zavření dne, kdy vyšel CPI nebo NFP (USA).
- R = výsledek / ATR20.
- Srovnání: stejné okno (zavření → zavření) ve všech ostatních dnech.
- Termíny: `kalendar_2010_2021.json` + `f7_lib` (od 9/2021). Vývoj 2010–2018.

**Pravidla rozhodnutí (u každého testu zvlášť), ANO jen když platí vše:**
1. Vývoj: signál > 0 a převis > 0 s t ≥ 2,0.
2. Kontrola: signál > 0 a převis > 0 s t ≥ 1,5.
3. Jiné trhy: převis > 0.
4. Broker 2019+: signál > 0 a převis > 0.
5. Převis kladný aspoň v 55 % let (Yahoo, celé období).

Skript `scratch/f55_f57.py`, výstup `research_data/f55/souhrn.txt`.
