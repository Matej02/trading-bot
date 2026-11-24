---
tags: [vyzkum, plan, sezonnost, krypto, ropa, rsi2]
datum: 2026-11-24
---
# F79 až F81: Halloween, RSI(2) na kryptu a na ropě

Zadání uživatele (2026-11-24): „…pokračuj i dál a dej mi, až najdeš třeba 5 věcí, které by mohly fungovat.“ Navazuje na [[F73 až F78 Dluhopisy, VIX a strach jako signál pro indexy|F73–F78]] (nic neprošlo). Plán je zapsaný **před výpočtem**, pravidla se po výsledku nemění.

**Proč:**
- **Halloween (Sell in May):** jeden z nejlépe doložených sezónních jevů (Bouman a Jacobsen 2002, potvrzeno v desítkách zemí). Obecnou měsíční sezónnost jsme testovali ([[F30 Měsíční sezónnost (průběžně)|F30]]), konkrétní pravidlo listopad–duben ne.
- **RSI(2) na kryptu a ropě:** RSI(2) funguje na US indexech ([[F42 RSI(2) přísná prověrka|F42]]), na kovech a měnách ne ([[F53 a F54 RSI(2) na kovech a měnách|F53, F54]]), ve světě ne ([[F66 až F68 Návrat k průměru (relativní, RSI(2) ve světě, noc po poklesu)|F67]]). Krypto a ropa netestované.
- Jen data, která už máme (bez stahování).

## F79 Halloween na indexech
- **Obchod:** long na otevření prvního obchodního dne měsíce, výstup na zavření posledního obchodního dne měsíce. Bez stopu (měsíční držení). R = výsledek / (3 × ATR20 při vstupu), jen pro měřítko.
- **Signál:** měsíce listopad až duben. **Srovnání:** všechny měsíce (stejný obchod).
- Náklady: půl spreadu na vstupu i výstupu, swap long za každou noc (středa 3×).
- **Trhy:** hlavní S&P 500, Nasdaq 100, Dow; jiné DAX, FTSE, CAC.
- **ANO jen když platí vše:**
  1. Vývoj (Yahoo do 2018): signál > 0, převis > 0, t ≥ 2,0.
  2. Kontrola (Yahoo 2019–2026): signál > 0, převis > 0, t ≥ 1,5.
  3. DAX, FTSE, CAC: převis > 0 u všech.
  4. Broker 2019–2026: signál > 0 a převis > 0.
  5. Převis kladný aspoň v 55 % let.

## F80 RSI(2) na kryptu
- **Pravidlo jako F42:** zavření > SMA200 a RSI(2) < 10 → long na otevření dalšího dne; výstup na zavření nad SMA5 nebo 10. den; stop 3 ATR20.
- **Krypto obchoduje i o víkendu:** denní svíčky ze všech 7 dní (dny UTC), swap za každou kalendářní noc.
- **Srovnání:** stejný obchod ze všech dní nad SMA200.
- **Data:** broker H1 → denní (BTCUSD od 2011, ETHUSD od 2016, LTCUSD od 2011, XRPUSD od 2016), Yahoo BTC-USD od 2014.
- **Náklady:** spread a swap brokera (BTC, ETH). LTC a XRP nemají údaje: spread 0,3 % ceny, swap jako BTC.
- **ANO jen když platí vše:**
  1. Vývoj (broker BTC 2012–2018): signál > 0, převis > 0, t ≥ 2,0.
  2. Kontrola (broker BTC 2019–2026): signál > 0, převis > 0, t ≥ 1,5.
  3. ETH, LTC, XRP (broker, celé období): převis > 0 u všech.
  4. Druhý zdroj Yahoo BTC 2015–2026: signál > 0 a převis > 0.
  5. Převis kladný aspoň v 55 % let (BTC broker).

## F81 RSI(2) na ropě
- **Pravidlo jako F42** (pracovní dny, spread a swap brokera; NATGAS bez údajů: spread 0,3 % ceny, swap 0).
- **Trhy:** hlavní WTI (`CRUDE_OIL`, Yahoo CL=F od 2000); jiné Brent (Yahoo od 2007) a zemní plyn (`NATGAS`, broker od 2023).
- **ANO jen když platí vše:**
  1. Vývoj (Yahoo WTI do 2018): signál > 0, převis > 0, t ≥ 2,0.
  2. Kontrola (Yahoo WTI 2019–2026): signál > 0, převis > 0, t ≥ 1,5.
  3. Brent (Yahoo celé období) a NATGAS (broker): převis > 0 u obou.
  4. Broker WTI 2019–2026: signál > 0 a převis > 0.
  5. Převis kladný aspoň v 55 % let (WTI Yahoo).

## Výsledek (2026-11-24, `scratch/f79_f81.py`, výstup `research_data/f79/souhrn.txt`)
**Neprošel žádný.**

| Test | Vývoj: signál / převis / t | Kontrola: převis / t | Broker / 2. zdroj | Jiné trhy převis | Kladné roky | Body |
|---|---|---|---|---|---|---|
| F79 Halloween | +0,305 R, převis +0,118, t 1,60 (n 293 měsíců) | −0,006 / −0,03 | +0,008 | DAX +0,187, FTSE +0,170, CAC +0,199 | 65 % | 3/5 |
| F80 RSI(2) krypto | −0,050 R, převis −0,062 | −0,030 | Yahoo −0,006 | ETH −0,027, LTC +0,023, XRP −0,037 | 14 % | 0/5 |
| F81 RSI(2) ropa | −0,025 R, převis −0,025 | +0,018 / 0,20 | broker +0,118 | Brent −0,035, NATGAS −0,102 (n 7) | 52 % | 1/5 |

**Co z toho plyne:**
- **Halloween** v Evropě drží celé období (převis +0,17 až +0,20 R za měsíc, t ~1,8–2,2). V USA je ale slabší (t 1,60 do 2018) a od 2019 nulový. Podle pravidel NE.
- **RSI(2) mimo US indexy nefunguje ani na kryptu, ani na ropě.** Návrat k průměru je vlastnost amerických akciových indexů, ne obecný jev.
