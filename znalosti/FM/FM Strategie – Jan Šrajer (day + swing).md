---
tags: [fm, zdroj, strategie, daytrading, swing]
zdroj: "D:\\youtube\\FM pdfka\\Strategie\\Jan Šrajer - Day Trading Strategie (PDF) + Swing Trading Strategie (PDF)"
zpracovano: 2026-10-29
---
# FM – Jan Šrajer: Day Trading (S/D 4H + M15 + likvidita) a Swing (S/D + makro skóre)

Autor základního kurzu ([[FM Základy tradingu]]). Day trading: 9 PDF, swing: 23 PDF. Viz [[FM materiály]].

## Day trading
- **Trhy a TF:** EURUSD a XAUUSD (jde i na většinu forexu). TF **4H → M15 → M5**. 3–5 obchodů týdně.
- **Časová okna (CET/CEST):** **8:30–9:30** (otevření Londýna), **10:30–11:30**, **13:30–16:00** (overlap LO–NY).
  Asie se neobchoduje ani nespravuje.
- **Udávané výsledky:** winrate 40–60 %, RRR **2–3,5R, průměr 2,7R**. Obchody pod 2R nebere.
  Efektivní RR počítá jako průměr TP1 a TP2.
- **Entry model** (všechny 4 podmínky musí platit):
  1. **M15 S/D level**
  2. **uvnitř 4H S/D levelu**
  3. **pivotní nebo lokální likvidita** (výběr)
  4. **premium/discount zóna** (short v premium, long v discount)
- **Doplňkové konfluence:** fundament, market structure, momentum na MTF/LTF a nPOC.
- **Tři modely z obrázků** (EURUSD M15) → [[Likvidita]], [[SFP – sweep likvidity]]:
  1. **Pivot equal highs liquidity:**
     - Trh je v downtrendu a nad cenou jsou dvě stejná high (LQ point 1 a 2).
     - Cena je sweepne a vletí do supply zóny. Následuje short ze zóny se SL nad zónou a RR ~3.
  2. **Equal highs liquidity:** totéž bez pivotu.
  3. **Pivot liquidity:**
     - Sweep předchozího pivot low, pak lokální změna trendu nahoru (MSS).
     - Vznikne local demand v místě sweepu, long na retestu demandu, cíl pivot high (RR ~3–4).
- **Rutina:**
  - Neděle: 4H struktura, 4H S/D, MTF momentum, zprávy, hlavní LQ body, nPOC, plán na Po–Út.
  - Ráno 7–8 h: totéž plus LTF momentum, M15 S/D, lokální likvidita a alerty.
  - Obchodují se jen levely z rána.

## Swing
- **Mechanický proces: LOKACE (HTF premium/discount) → TREND (HTF) → SETUP (LTF entry, SL, TP).**
- **Timeframy:**

  | Držení | HTF | LTF |
  |---|---|---|
  | hodiny → dny | Denní | 8h–2h, ideálně **4h** |
  | dny → týdny | Týdenní | Denní–10h, ideálně **Daily** |
  | týdny → měsíce | Měsíční | Týdenní |

  „Větší TF = větší imbalance = víc nevyplněných příkazů = vyšší pravděpodobnost.“
- **Pravidla S/D zóny** → [[Supply a demand zóny]]:
  - Zóna je **unmitigated**, tedy nejbližší neotestovaná na HTF. **Mitigace může zasáhnout nejvýš 25 % zóny.**
  - **Po zóně musí následovat impulzivní svíčka, která „něco dokázala“: prolomila high nebo low.**
  - **Pivot > local.** Alternativní postup: „vše, co vypadá jako S/D zóna, je S/D zóna“.
- **Premium/discount:**
  - Fibo **0,333 / 0,5 / 0,666** mezi supply (od spodní hrany) a demand (od horní hrany) na HTF.
  - **Top discount** = long, **top premium** = short. Stačí 2R.
  - Potom zkontrolovat neotestované zóny na LTF (4h).
  → [[Premium a discount]]
- **Fibonacci retracement:**
  - Úrovně 23,6 / 38,2 / 50 / 61,8 / 66 / 78,6 / 88,6.
  - První je 0,382; když padne, cena míří ke **golden pocket 0,618–0,66**. Swing chce hlubší retracementy.
- **Set and forget:** entry, SL a TP předem, bez zásahů.

## Makro skóre (Trading Analyzer) → [[Makro skóre měn]]
Skóre každé měny (EUR, GBP, USD, AUD, NZD, CAD, CHF, JPY) se skládá ze složek; skóre páru je jejich součet:

| Složka | Rozsah | Poznámka |
|---|---|---|
| COT | −3…+3 | pozice velkých hráčů (leveraged funds, asset managers) |
| Retail sentiment | −1…+1 | **kontrariánsky** (retail long → medvědí) |
| GDP | −2…+2 | |
| CPI | −3…+3 | vyšší inflace je býčí (sazby porostou) |
| Zaměstnanost | −4…+4 | NFP, nezaměstnanost |
| Úrokové sazby | −2…+2 | očekávání sazeb |
| Manufacturing PMI | −2…+2 | 50 = hranice |
| Services PMI | −2…+2 | Kanada hlavně manufacturing |
| Retail sales | −2…+2 | |
| Sezónnost | −2…+2 | 10 let historie |
| Trend | −2…+2 | technický |

- **Bias páru:** −18…−9 velmi medvědí, −8…−5 medvědí, −4…+4 neutrální, +5…+8 býčí, +9…+18 velmi býčí.
- **Rozhoduje změna skóre, ne hodnota.** Trade idea = **změna o ≥ 2 body**.
  Potom zóny ve směru změny, počkat na pullback a dát SL pod zónu.
  Příklad: USDJPY stojí, skóre −4 → −1 → long.
- **Sezónnost:** JPY posiluje v březnu (repatriace), CAD v zimě (ropa).

## Testovatelnost
- **Day trading:** M15 zóna uvnitř 4H zóny, sweep likvidity a premium/discount. Testovatelné na M15 z MT5.
  Je to blízké F7 S1 ([[SFP – sweep likvidity]]), ale s 4H zónou a vstupem ze zóny místo FVG.
- **Swing:** HTF neotestovaná zóna s impulzem, který prolomil high/low, a lokace v top discountu/premiu. Testovatelné na D1/W1.
- **Makro skóre:** jde postavit z volných dat (FRED, CFTC, kalendář), ale s velkou prací. Je to kandidát na samostatný výzkum,
  srovnání s [[Carry]] a [[COT]] z v1–v6.

## Z grafů v PDF (prohlédnuto všech obrázků, 2026-10-29)
- **Swing S/D na EURUSD D1:**
  - Supply (Daily TF) je pásmo na začátku poklesu, demand (Daily TF) pásmo u dna.
  - Mezi ně se natáhne Fibo: **Top Premium = supply zóna**, Premium 0,666–1, „Rovnováha mezi S&D“ 0,333–0,666, Discount 0–0,333, **Top Discount = demand zóna**.
  - Na příkladech **cena odskočí od Top Discount** (kroužek u demand) **až do Premium** a tam se odrazí dolů.
    Obchoduje se tedy rozpětí mezi D zónami: long z demand s cílem v premium nebo supply, short ze supply s cílem v discount nebo demand.
  - Uvnitř jsou ještě LTF (4H) zóny (modré pásy).
- **Day trading entry model 2 (Equal highs liquidity):**
  - Nad trhem supply level a pod ním **equal highs „pro tvorbu LQ“**.
  - Cena sweepne equal highs i lokální LQ a vletí do supply. Následuje **short ze supply**, SL nad zónou a TP na 0,5 Fibo i níž.
  - Popisky: „Local LQ slouží jako bod pro výběr“, „Výběr LQ“, „0.5 Fibo“.
- **Entry model 1 a 3:** viz text výše (EURUSD M15, 14. 3. 2024). RR na obrázcích ~3–4.
- **Score overview:** po změně skóre retest zóny (šedá linie) a short se SL nad zónou. Tabulka skóre všech párů obsahuje sloupce Score, COT, Retail sentiment a Seasonality.
- **COT (EUR, USD):** zakroužkované extrémy, kde se long a short křivky protnou nebo rozevřou, předcházejí otočkám.

## Otestováno – F10 (2026-10-29)
Entry model přesně podle PDF na minutových datech, OOS 2022–26: **day trading −0,29 R (n 97)**, bez výhody. → [[F10 Entry modely mentorů FM]]
