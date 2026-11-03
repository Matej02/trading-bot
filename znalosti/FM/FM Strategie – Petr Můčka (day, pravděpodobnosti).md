---
tags: [fm, zdroj, strategie, daytrading]
zdroj: "D:\\youtube\\FM pdfka\\Strategie\\Petr Můčka - Day Trading Strategie (PDF)"
zpracovano: 2026-10-29
---
# FM – Petr Můčka: Day Trading (pravděpodobnostní levely + S/D/FVG + entry M1/M5)

26 PDF, 198 stran. Obchoduje EURUSD, XAUUSD a NQ (jde i na GBPUSD a XAGUSD), intraday bez držení přes noc.
Krypto obchoduje na Bybitu. 1. místo v CZ turnaji FundedNext, 40. místo z 72 000 v turnaji TradingView 11/2024.
Strategie je postavená na „pravděpodobnostech a statistikách“. Viz [[FM materiály]].

## Pravděpodobnostní levely (jádro strategie)
- **Pro TP:** daily close svíček (směr), **Asia High/Low**, **close VWAP předchozího dne**, **nPOC z předchozího dne**,
  pohyb v range mezi VAH a VAL.
- **Pro vstup:** **Frankfurt session na zlatě** (8–9), daily, weekly a monthly close svíček.
- **Svíčka jako bias** → [[Daily bias]]:
  - **Po bearish denní svíčce cílí na low předchozího dne, po bullish na high** („velká pravděpodobnost trefení“).
  - Totéž s W a M svíčkami. Bias se během dne nemění.
- **Asie jako zdroj likvidity:**
  - V Londýně se často vybere Asia high nebo low a cena pak jde opačně.
  - **Platí jen, když má asijský range ≤ 35 pipů** (EURUSD).
- **Zprávy:**
  - Před zprávou bývá konsolidace, pak výběr likvidity a velký pohyb na druhou stranu. Odhad směru podle pohybu před zprávou sedí **„v 7 z 10 případů“**.
  - Průměrné pohyby EURUSD za prvních 15 min: CPI 59,8 pipu, FED 59,9, NFP 56,8, ECB 34,7, PMI 26–27, retail sales 25, GDP 25, PPI 20, nezaměstnanost 20, PCE 17.
  → [[Zprávy a kalendář]]

## Entry model → [[MSS a displacement]], [[FVG]]
1. **Předem připravené zóny** (4H/M15): S/D, OB, FVG, balanční levely, likvidita, fixed range.
2. **Structure shift na M1 nebo M5** s velkým momentem. Může to být i průraz nejbližší S/D zóny. **CHoCH nedoporučuje.**
   - **M1** u A+ zón (rychle napozicovat).
   - **M5** u A/B setupů (větší změna struktury).
3. **Vstup limitem (90 %)** lehce před zónu kvůli spreadu. Zóna je golden pocket (61,8 %) nebo **FVG na M5**.
4. **SL 8–12 pipů** (EURUSD, podle volatility), **nikdy pod 6 pipů**, **přímo na high/low** bez rezervy.
   Důvody: lepší RRR, rezerva je stejně odhad a při zprávách je „první ve frontě“ a má menší skluz.
5. **TP:** Asia H/L, close VWAP, nPOC, daily close, likvidita, S/D, dOPEN, Fibonacci.
6. **Killzones:** obchoduje jen **9:00–11:00 a 13:30–17:00** (CET).
   Session boxy: Asie 2–6, Frankfurt 8–9, Londýn 9–17, NY 14–22.

## Definice
- **Balanční level** = protažený BOS. Slouží jako entry, konfluence i target, na všech TF.
  Cena odražená od balančního levelu i po výběru likvidity znamená pokračování trendu.
- **S/D:** zóna před impulzivním pohybem. **Když zóna způsobila BOS, je pravděpodobnost odrazu větší.**
  **SL nikdy přímo nad zónu** („trh si pro ty SL chodí“). Kreslí se knot až tělo, kontrola na vyšším TF (i W).
  → [[Supply a demand zóny]]
- **OB:** poslední opačná svíčka před impulzem. S/D je „poslední svíčka, kde se akumulovalo“. Nejlepší je kombinace obou.
- **FVG:** reakce na **50 %** FVG. Gap se musí zaplnit celý a slouží jako target, ne vstup. FVG ve směru trendu, jinak magnet pro TP.
- **Fibonacci:** 61,8 % je nejsilnější. SL lze dát na 33 %. Negativní Fibo slouží jako swing targety.
- **Objem:** svíčka výběru likvidity musí být „stažená“ (velký objem). Objem roste na otevření LO a NY.
  Composite VP: cena mimo zónu se rychle přesune k další likviditě.
- **COT:** extrémní short + dlouhodobý support = možný odraz. Rostoucí open interest s net pozicemi posiluje trend.
- **Risk:** po 5 ztrátách v řadě porovnat deník s plánem.

## Testovatelnost
- **Daily bias ze svíčky** (bearish D → cíl PDL) je testovatelný na D1 a dá se spojit s pravidlem Veselovského ([[Daily bias]]).
- **Asia range ≤ 35 pipů → sweep v Londýně → opačný směr** jde testovat na M5/M15 EURUSD. Je to [[SFP – sweep likvidity]] s filtrem šířky Asie.
- Frankfurt session na zlatě = pravděpodobnostní level pro vstup (bez definice, ověřit).

## Z grafů v PDF (prohlédnuto všech obrázků, 2026-10-29)
Obrázky z PDF (všechny grafy, po lekcích): [[FM obrázky – Petr Můčka (day)]] (196)

- **Trading plán „TECH“** (OCR z Notionu):
  - Rating: **EPIC** = nejlepší trade 1:3, **CLASIC** = normální trade 1:2, BUG = špatný trade.
  - Strategie: **FLOW + SFP + KEY level + FB + ABSORBCE**:
    - jen když je trap,
    - pravidla exitu u LIQ,
    - použít, kde je výběr LIQ,
    - SFP,
    - **15min + 5min svíčka = vstup**.
- **Kreslení S/D (EURUSD H4):**
  - Zóny jsou šedé pásy u míst, odkud vyšel impulz.
  - **Platné jsou jen zóny, z nichž pohyb udělal BOS** (zelené fajfky). Zóny uvnitř pomalého driftu bez BOS jsou přeškrtnuté (červené X).
  - Na příkladech **první retest zóny = obrat** (šipka). Demand se testuje po pullbacku k trendline.
- **Doporučené TF pro S/D:** forex, akcie a komodity 5m, 15m, H1, H4, D1, W1; krypto 5m–D1; opce D1/H4; dluhopisy D1/W1.
- **OB vs S/D** (tabulka):
  - OB = jedna svíčka, velmi přesný, slouží k přesnému vstupu.
  - S/D = širší zóna akumulace, slouží k identifikaci oblasti obratu.
- **Daily bias ze svíčky:** po bearish D svíčce oranžová čára ke včerejšímu low (target), po bullish k high. Na 6 příkladech target trefen.
- **Session target:** „EURUSD slouží jako ideální target, **pravděpodobnost, že vyplníme toto High i Low během dne**“.
  Box = range Asie nebo Frankfurtu, cílí se na obě strany.
- **Balanční level:** horizontála z protaženého BOS. Cena se k ní vrací (retest) a pokračuje v trendu.
- **FVG typy** (tabulka): bullish, bearish, HTF (H4/D1 má větší váhu), LTF (M15/M5), reversal FVG, FVG u likvidity, FVG s nízkou likviditou (mimo seance).
  Gap se rozlišuje (otevření po víkendu nebo zprávách).
- **Killzones** (GMT): London 07–10, NY 13–16, Asian 23–02, **London Close 16–17 (návrat k D open u EURUSD)**.
- **Entry model:**
  - Na 1m/5m MSS po vstupu do zóny HTF, pak vstup limitem na retest. TP velký box, RR ~3–7 (2,74 a 2,73 na ukázkách).
  - SL přímo na high: „první ve frontě, ztráta 1,4 % místo 3,7 %“.
- **Equity křivka** statistik je hladce rostoucí bez zdroje dat (marketing).
- **COT EUR:** report z 4. 2. 2025, commercials long 348k / short 311k, změna −6 476 / −1 352.
- **Zprávy:** 674 obchodů kolem zpráv, 40,8 % vs 59,2 % (bez popisu, co je co).

## Doplněno uživatelem (2026-11-03)
Viz [[Doplňující pravidla k FM PDF]], B1 (struktura: swing, BOS tělem, strong/weak, stáří; entry model 0,618–0,66 / FVG).

## Otestováno – F10 (2026-10-29)
Entry model přesně podle PDF na minutových datech, OOS 2022–26: **−0,23 R (n 5 150)**, bez výhody. → [[F10 Entry modely mentorů FM]]

## Otestováno – F12 (2026-11-03)
Podle doplňujících pravidel uživatele, po prohlédnutí všech 196 obrázků: nejlepší varianta vývoj −0,18 R, OOS +0,06 R, náhoda −0,08 R; bez výhody. → [[F12 Můčka podle doplňujících pravidel]]
