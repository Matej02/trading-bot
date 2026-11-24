---
tags: [vyzkum, plan, krypto, indexy, fomc]
datum: 2026-11-24
---
# F82 až F84: víkend bitcoinu, slabý měsíc a cyklus FOMC

Zadání uživatele (2026-11-24): „Ano, přidej je do simulátoru a pokračuj zase dál.“ Plán je zapsaný **před výpočtem**, pravidla se po výsledku nemění. Jen data, která už máme.

**Proč tyhle tři:**
- **F82:** víkendový gap na měnách (F72) se hrubě zavíral, ale sežral ho nedělní spread. Bitcoin se o víkendu obchoduje, takže spread v neděli není široký. Mezi obchodníky je známé „zavírání CME gapu“ (pohyb přes víkend se vrací). Netestováno.
- **F83:** jediná rodina, která funguje, je „kupovat strach na indexech“ (RSI(2) na dny, F76 VIX). Měsíční horizont jsme netestovali: po velmi slabém měsíci long na celý další měsíc. Méně se překrývá s RSI(2).
- **F84:** Cieslak, Morse a Vissing-Jorgensen (Journal of Finance 2019): akcie vydělávají hlavně v „sudých týdnech“ cyklu FOMC (týden 0, 2, 4, 6 od zasedání). Drift před FOMC (F31) je jen týden 0. Celý cyklus jsme netestovali. Termíny FOMC máme od 2010.

## F82 Víkendový pohyb bitcoinu (návrat k pátku)
- **Páteční cena** = zavření hodinové svíčky 20:00–21:00 UTC v pátek (zavření CME). **Vstup** = otevření svíčky 23:00 UTC v neděli (otevření CME).
- **Víkendový pohyb** W = vstup − páteční cena. **Signál:** |W| ≥ 0,5 × ATR20 (denní svíčky UTC).
- **Obchod proti W:** cíl = páteční cena, stop = stejná vzdálenost na druhou stranu (1:1), jinak výstup po 120 hodinách za zavírací cenu. Svíčka se stopem i cílem → stop.
- **R** = |W|. **Náklady:** spread brokera (BTC 23,9 $), swap za každou noc (long i short podle brokera). ETH podle brokera; LTC a XRP spread 0,3 % ceny, swap jako BTC.
- **ANO jen když platí vše:**
  1. Vývoj (broker BTC 2012–2018): čistý průměr R > 0, t ≥ 2,0.
  2. Kontrola (broker BTC 2019–2026): čistý průměr R > 0, t ≥ 1,5.
  3. Druhý zdroj (Binance BTCUSDT 1h 2019–2026): čistý průměr R > 0.
  4. Jiné trhy ETH, LTC, XRP (broker, celé období): čistý průměr > 0 aspoň u 2 ze 3.
  5. Kladný čistý výsledek aspoň v 55 % let (BTC broker).

## F83 Slabý měsíc na indexech → long další měsíc
- **Signál** na zavření posledního obchodního dne měsíce: měsíční výnos indexu ≤ 20. percentil měsíčních výnosů za předchozích 120 měsíců (aspoň 60 měsíců historie).
- **Obchod:** long na otevření prvního obchodního dne dalšího měsíce, výstup na zavření posledního obchodního dne toho měsíce. Bez stopu. R = výsledek / (3 × ATR20), jen pro měřítko.
- **Srovnání:** stejný obchod ve všech měsících. Náklady: půl spreadu na vstupu i výstupu, swap long za noc.
- **Trhy:** hlavní S&P 500, Nasdaq 100, Dow; jiné DAX, FTSE, CAC.
- **ANO podle standardních 5 bodů** (jako [[F73 až F78 Dluhopisy, VIX a strach jako signál pro indexy|F73–F78]]): vývoj Yahoo do 2018 t ≥ 2,0; kontrola 2019–2026 t ≥ 1,5; DAX, FTSE, CAC převis > 0 u všech; broker 2019–2026 signál > 0 a převis > 0; převis kladný aspoň v 55 % let.

## F84 Sudé týdny cyklu FOMC
- **Den 0** = den oznámení FOMC (termíny 2010–2026 jako F31). Okna po 5 obchodních dnech: dny −1 až +3 (týden 0), +9 až +13 (týden 2), +19 až +23 (týden 4), +29 až +33 (týden 6). Okno se bere, jen když skončí před dnem −1 dalšího zasedání.
- **Obchod:** long na otevření prvního dne okna, výstup na zavření posledního dne okna, pojistný stop 3 ATR20.
- **Srovnání:** stejný 5denní obchod ze všech dní. Náklady jako F83.
- **Trhy:** hlavní S&P 500, Nasdaq 100, Dow; jiné DAX, FTSE, CAC.
- **ANO podle standardních 5 bodů:** vývoj Yahoo 2010–2018 t ≥ 2,0; kontrola 2019–2026 t ≥ 1,5; DAX, FTSE, CAC převis > 0 u všech; broker 2019–2026 signál > 0 a převis > 0; převis kladný aspoň v 55 % let.

## Výsledek (2026-11-24, `scratch/f82_f84.py`, výstup `research_data/f82/souhrn.txt`)
**Neprošel žádný.**

### F82 Víkendový pohyb bitcoinu → NE (0/5)
- Broker BTC 2012–18: n 35, hrubě −0,04 R, čistě −0,17 R. 2019–26: n 109, čistě −0,06 R. Binance 2019–26 −0,07 R.
- ETH −0,24 R, LTC +0,02 R, XRP −0,12 R; kladné roky 40 %.
- Pohyb bitcoinu přes víkend se nevrací ani hrubě. „Zavírání CME gapu“ se nepotvrdilo.

### F83 Slabý měsíc → long další měsíc → NE (2/5)
- Vývoj (do 2018): signál +0,28 R za měsíc, převis +0,09 R (t 0,87). Kontrola 2019–26: převis +0,24 R (t 0,98, n 28). Broker: převis +0,71 R (jen 6 měsíců).
- DAX −0,04, FTSE +0,12, CAC +0,14; převis kladný v 64 % let.
- Po slabém měsíci index v dalším měsíci v průměru roste víc než jindy, ale rozptyl je velký a t daleko od hranice.

### F84 Sudé týdny cyklu FOMC → NE (1/5)
- Vývoj 2010–18: převis +0,05 R (t 1,48). Kontrola 2019–26: −0,03 R. Broker −0,02 R. Kladné roky 47 %.
- Efekt z literatury (data do 2016) od 2019 zmizel.
