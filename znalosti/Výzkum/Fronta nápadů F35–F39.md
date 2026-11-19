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

## Výsledky F36 a F37 (2026-11-19)
Souhrn: `research_data/f36_f37/souhrn.txt`. Převis = průměr R v události − průměr R ostatních dní nebo týdnů (průměr SPX a NAS, náklady brokera).

| Test | Vývoj 1990–2018 | Kontrola 2019–26 | Broker 2019+ | US30 / DAX | Roky s převisem | Verdikt |
|---|---|---|---|---|---|---|
| **F37** den před svátkem | převis −0,003 R (t −0,09) | **+0,133 R (t 2,11)** | +0,086 R | +0,021 / +0,124 | 59 % | **BEZ VÝHODY** (bod 1 NE) |
| **F36** týden OPEX | převis +0,138 R (t 1,44) | −0,256 R (t −1,30) | −0,400 R | +0,177 / −0,083 | 62 % | **BEZ VÝHODY** (body 1–4 NE) |

- **F37:** ve vývoji 1990–2018 žádný převis. Kladný je až zhruba od 2007 a v kontrole 2019–2026. Je to podobný obrázek jako u [[F31 Drift před FOMC|F31]], ale podle pravidel zapsaných předem neprošel. Pravidla se dodatečně nemění. Jen popis: v posledních letech kladný, nic víc.
- **F36:** efekt z literatury v datech 1990–2018 slabý (t 1,44) a po 2019 obrácený. Zřejmě zmizel, když se o něm vědělo.
- Další na řadě: F39 (momentum bez měn). F35 a F38 čekají na souhlas se stažením dat.

## F35 a F38: plán (zapsán PŘED výpočtem, 2026-11-19)
**Data (staženo se souhlasem uživatele 2026-11-19 „ano stáhni data a pokračuj“):**
- HistData M1 EURUSD, GBPUSD, USDJPY 2010–2025, DAX (GRXEUR) 2010–2025, EuroStoxx (ETXEUR) 2010–2019, v `research_data/histdata/zip_fx`. Čas HistData = EST bez letního času (UTC−5), ověřuje se na páteční uzávěrce.
- Termíny ECB (tiskové konference po měnověpolitickém zasedání) 2005–2026 z ecb.europa.eu v `research_data/f38/ecb_terminy.txt`. Vyřazeno 26. 10. 2014 (stress test, ne rozhodnutí) a 8. 7. 2021 (revize strategie).
- Broker H1 2019–2026 s posunem času jako v `f2x_lib` (+1 h v britském letním čase).

**F35 Měsíční fixing v FX:**
- **Den:** poslední pracovní den měsíce s daty.
- **Signál:** rozdíl = výnos S&P 500 − výnos EuroStoxx 50 (Yahoo, místní měna) od zavření posledního dne předchozího měsíce do zavření předposledního pracovního dne. Obchod jen při |rozdíl| ≥ 1 p. b.
- **Směr:** US vedly (rozdíl > 0) → slabší USD → long EURUSD a GBPUSD, short USDJPY. Opačně naopak.
- **Okno:** 10:00 → 16:00 Londýn (fixing WM/R v 16:00).
- **Náklady:** spread brokera podle londýnské hodiny. R = výsledek / ATR20 denního rozpětí.
- **ANO jen když platí vše:**
  1. Vývoj (HistData 2010–2018) EURUSD > 0 a t ≥ 2,0.
  2. Kontrola (broker 2019–2026) EURUSD > 0 a t ≥ 1,5.
  3. GBPUSD i USDJPY (celé období) > 0.
  4. Druhý zdroj (HistData 2019–2025) EURUSD > 0.
  5. Lepší než stále long EURUSD ve stejném okně a měsících, ve vývoji i v kontrole.

**F38 Drift před ECB:**
- **Obchod:** long DAX od 13:30 Praha v předchozí pracovní den do 13:30 Praha v den rozhodnutí. Rozhodnutí se zveřejňuje ve 13:45, od 2022 ve 14:15.
- Broker H1: 13:00 → 13:00 Praha.
- **Náklady:** spread a swap (noc ze středy na čtvrtek 3×).
- **Srovnání:** stejné 24h okno ve všech ostatních pracovních dnech. Rozhoduje převis nad driftem.
- **ANO jen když platí vše:**
  1. Vývoj (HistData DAX 2010–2018): událost > 0 a převis > 0, t ≥ 2,0.
  2. Kontrola (broker DAX 2019–2026): událost > 0 a převis > 0, t ≥ 1,5.
  3. EuroStoxx (HistData 2010–2018) i CAC (broker 2019+): převis > 0.
  4. Druhý zdroj (HistData DAX 2019–2025): převis > 0.
  5. Převis kladný aspoň v 55 % let.

Skript `scratch/f35_f38.py`, výstup `research_data/f38/souhrn.txt`.

## Výsledky F35 a F38 (2026-11-19)
Souhrn: `research_data/f38/souhrn.txt`, skript `scratch/f35_f38.py`.
- **Oprava před výsledkem:** čas HistData FX a indexů je **New York včetně letního času**, ne pevný EST. Ověřeno na páteční uzávěrce: 16:59 NY v zimě i v létě. První běh s pevným EST byl v létě o hodinu posunutý. Platí jen druhý běh, pravidla rozhodnutí se neměnila.

| Test | Vývoj 2010–18 | Kontrola 2019–26 | Druhý zdroj | Jiné trhy | Verdikt |
|---|---|---|---|---|---|
| **F35** fixing FX (EURUSD) | −0,105 R (t −1,63) | +0,003 R (t 0,04) | +0,020 R | GBPUSD −0,040, USDJPY +0,040 | **BEZ VÝHODY** (body 1, 2, 3, 5 NE) |
| **F38** drift před ECB (DAX, převis) | **+0,218 R (t 3,21)**, výhra 70 % | +0,045 R (t 0,45) | −0,151 R* | EuroStoxx +0,196 (t 2,27), CAC +0,105 | **BEZ VÝHODY** (body 2 a 4 NE) |

- **F35:** žádný efekt fixingu ve směru podle rozdílu výkonu akcií. Ve vývoji spíš opačně.
- **F38:**
  - 2010–2018 velmi silný (70 % výher, i na EuroStoxx), od 2019 slabý (+0,045 R). Roky s převisem 13 z 16.
  - Je to zrcadlo F31 (tam slabé do 2018, silné od 2019). Podle pravidel neprošel, pravidla se nemění.
  - *Bod 4 kazí 2 chybné ticky v HistData DAX 2019+ (skok cen ×3,7, 2020-06-15 a 2023-12-03), které nafukují „ostatní dny“. Ani bez nich by ale nevyšel bod 2 (kontrola t 0,45), verdikt se nemění.
- **Poučení pro metodiku:** u HistData předem filtrovat chybné ticky (skok > 20 % za minutu).

## F39 Momentum bez měn: plán (zapsán PŘED výpočtem, 2026-11-19)
- **Trhy (13):**
  - indexy SPX500, NAS100, US30, DAX, CAC, IBEX, FTSE, EuroStoxx;
  - kovy XAU, XAG, XPT;
  - ropa WTI a Brent.
  - Bez FX a krypta, protože tam výhodu zabíjí swap.
- **Pravidlo jako [[Momentum L=250]]:** pozice v den t = znaménko výnosu za 250 dní ke zavření t−1. Drží se do otočení, bez TP.
- **Model:** denní výnos pozice / σ60 (směrodatná odchylka denních výnosů do t−1), každý trh stejné riziko. Portfolio = průměr trhů v daný den.
- **Náklady:**
  - spread brokera při každé změně směru;
  - swap brokera za každou noc (ze středy na čtvrtek 3×), podle směru.
  - Dnešní swapy se používají i pro minulost, což je konzervativní.
- **Data:**
  - vývoj Yahoo denní 1990–2018;
  - kontrola Yahoo 2019–2026;
  - druhý zdroj broker H1 → denní 2019–2026.
- **ANO jen když platí vše:**
  1. Vývoj: průměr portfolia > 0, t ≥ 2,0.
  2. Kontrola > 0, t ≥ 1,5.
  3. Broker 2019+ > 0.
  4. Lepší než stále long stejné trhy (se stejnými náklady) ve vývoji i v kontrole.
  5. Indexy i komodity zvlášť > 0 za celé období.
- Skript `scratch/f39_mom.py`, výstup `research_data/f39/souhrn.txt`.

## Výsledek F39 (2026-11-19)
Souhrn: `research_data/f39/souhrn.txt`, skript `scratch/f39_mom.py`.

| Část | Momentum | Stále long |
|---|---|---|
| Vývoj Yahoo 1990–2018 | +0,0221 R/den, t 3,01, Sharpe 0,55 | +0,0247, Sharpe 0,55 |
| Kontrola Yahoo 2019–2026 | +0,0033, t 0,27, Sharpe 0,10 | +0,0319, Sharpe 0,74 |
| Broker 2019–2026 | +0,0128, Sharpe 0,31 | +0,0434, Sharpe 0,72 |

- Indexy i komodity zvlášť jsou kladné (Sharpe 0,35 a 0,40), ale **nikde nejsou lepší než prosté držení.**
- **BEZ VÝHODY** (body 2 a 4 NE). Bez měn momentum jen kopíruje růst trhu, a to hůř. Potvrzuje to [[Momentum L=250]].

## Shrnutí vlny F35–F39 (2026-11-19)
- **Neprošlo nic:**
  - F35 fixing FX;
  - F36 OPEX;
  - F37 den před svátkem (silné jen od 2019);
  - F38 ECB (silné jen do 2018);
  - F39 momentum bez měn.
- **Vzorec:** kalendářní efekty z literatury jsou silné v jednom období a v druhém mizí (F31, F37, F38). Proto jsou důležité kontrola na novějších letech a pravidla předem. Jinak bychom si vybírali náhodu.
- **Návrh dalšího kroku:** místo dalších nových nápadů rozšířit to, co prošlo:
  - **F33 na další indexy.** US30 a DAX jsou už v testu kladné (+0,345 a +0,220 R), takže víc obchodů ze stejné ověřené výhody;
  - nová kontrola F31 na DAX/EuroStoxx kolem FOMC.
  - Rozhoduje uživatel.
