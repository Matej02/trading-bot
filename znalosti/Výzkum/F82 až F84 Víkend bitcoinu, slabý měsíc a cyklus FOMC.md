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

## Výsledek
(doplní se po výpočtu)
