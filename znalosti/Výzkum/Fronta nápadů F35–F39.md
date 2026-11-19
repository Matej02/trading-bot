---
tags: [vyzkum, fronta, plan]
datum: 2026-11-19
---
# Fronta nápadů F35–F39

Zadání uživatele (2026-11-19): „Ano, začni s výzkumem.“ Cíl je krok 1 z [[Cesta k prop účtu]]: víc ověřených strategií. Bot se nemění, postup jako u [[Fronta nápadů F22–F33|F22–F33]] (plán předem, starší roky, kontrola, druhý zdroj, jiné trhy, náklady brokera, korelované trhy po událostech).

## Nejdřív: otázka ze 14. 11. (swapy TRY u momenta)
Je už zodpovězená ve vaultu:
- [[Momentum L=250]] měl hrubou výhodu (holdout t 3,3), ale polovina byl úrok za držení a zbytek sebere přirážka ve swapu brokera. Holdout PF 0,98 ([[F1 Nové třídy signálů|F1]], [[Carry]], [[Náklady brokera]]).
- **Swapy test započítal. Momentum u tohoto brokera výhodu nemá.**
- V simulátoru běží jen proto, že režim „bere co jde“ pouští všechny systémy. Ztráty z momenta a swapy TRY (−70 $ denně) jsou tedy očekávané, ne chyba.
- Vypnutí momenta v simulátoru je rozhodnutí uživatele, bot se teď nemění.

## Proč tyhle nápady
Co zatím prošlo ([[F33 Rebalancování na konci měsíce|F33]], [[F31 Drift před FOMC|F31]]), má společné tři věci:
- **kalendářní událost s doloženým tokem peněz** (rebalancování fondů, Fed);
- **málo obchodů**, takže náklady nehrají roli;
- **krátké držení.**

Technické vzorce (F22–F28) neprošly. Další nápady jsou proto ze stejné rodiny, ale na jiných událostech nebo trzích. Musí být nezávislé na F33 a F31.

| # | Nápad | Pravidlo (návrh) | Proč | Data |
|---|---|---|---|---|
| **F35** | Měsíční fixing v FX (rebalancování zajištění) | Poslední obchodní den měsíce: když US akcie v měsíci předběhly evropské, long EURUSD 12:00 → 16:00 Londýn (fixing WM/R), jinak short | Zahraniční investoři dorovnávají měnové zajištění (Melvin a Prins 2015). Je to F33 na měnách, nekoreluje s indexy | broker H1 FX 2019–26. **Vývoj 2010–18 potřebuje stáhnout HistData FX M1 (zeptat se)** |
| **F36** | Týden expirace opcí (OPEX) | Long indexů od zavření pátku před týdnem expirace do zavření pátku expirace (3. pátek v měsíci) | Zajišťování dealerů opcí táhne trh nahoru (Stivers a Sun 2013). 12× ročně | Yahoo denní od 1990, broker 2019+ |
| **F37** | Den před svátkem | Long indexů v obchodním dni před zavřenou burzou v NY (zavření → zavření) | Jeden z nejstarších kalendářních efektů (Ariel 1990). Asi 9× ročně | Yahoo denní od 1990, broker 2019+ |
| **F38** | Drift před ECB | Long DAX a EuroStoxx 24 h před rozhodnutím ECB | Obdoba F31 v Evropě (Lucca a Moench uvádí slabší efekt). Asi 8× ročně | broker + Yahoo. **Termíny ECB 2010–2026 stáhnout z ecb.europa.eu (zeptat se)** |
| **F39** | Momentum bez měn | [[Momentum L=250]] jen na indexech, kovech a energiích (bez FX a krypta) | Hrubá výhoda momenta existuje, u FX ji zabíjí swap. Ověřit, jestli zbytek nese čistou výhodu | broker H1 → D1 2019–26, Yahoo denní |

**Pořadí:** F37 a F36 hned (data máme). Pak F39. F35 a F38 až po souhlasu se stažením dat.

## F36 a F37: plán (zapsán PŘED výpočtem)
**Společné:**
- **Data:**
  - vývoj Yahoo denní 1990–2018;
  - kontrola Yahoo 2019–2026;
  - druhý zdroj H1 brokera → denní 2019–2026;
  - jiné trhy US30 a DAX (Yahoo, celé období).
- **Kalendář** obchodních dní a svátků podle S&P 500 z Yahoo.
- **Náklady:** půl spreadu brokera na vstupu i výstupu a swap za každou noc (středa 3×).
- **R** = výsledek / ATR20 denního rozpětí, bez stopu.
- **Hodnotí se po událostech** (průměr SPX500 a NAS100), ne po obchodech.
- **Srovnání** (indexy dlouhodobě rostou, takže samotné „> 0“ nestačí): stejná délka držení ve všech ostatních dnech, resp. týdnech. Rozhoduje **převis nad driftem** (událost − ostatní).

**F37 Den před svátkem:**
- Svátek = pracovní den, kdy NYSE nebyla otevřená.
- Neplánované zavření se vyřazuje: 11.–14. 9. 2001, 11. 6. 2004, 2. 1. 2007, 29.–30. 10. 2012, 5. 12. 2018, 9. 1. 2025.
- Obchod: long od zavření dne T−1 do zavření dne T (T = poslední obchodní den před svátkem).
- Srovnání: všechny ostatní dny, zavření → zavření.

**F36 OPEX:**
- Pátek expirace = 3. pátek v měsíci. Když je svátek, platí poslední obchodní den před ním.
- Obchod: long od zavření posledního obchodního dne před pondělím týdne expirace do zavření pátku expirace.
- Srovnání: všechny ostatní týdny (pátek → pátek).

**Pravidla rozhodnutí (u každého testu zvlášť), ANO jen když platí vše:**
1. Vývoj: událost > 0 a převis nad ostatními dny/týdny > 0 s t ≥ 2,0 (Welch).
2. Kontrola: událost > 0 a převis > 0 s t ≥ 1,5.
3. US30 i DAX: převis > 0 (celé období).
4. Druhý zdroj (broker 2019+): převis > 0.
5. Po letech: převis kladný aspoň v 55 % let.

Skript `scratch/f36_f37.py`, výstup `research_data/f36_f37/souhrn.txt`.
