---
tags: [vyzkum, f25, pary, relativni-hodnota]
datum: 2026-11-07
---
# F25 Párové obchody (relativní hodnota)

Z [[Fronta nápadů F22–F33|fronty nápadů]]. Jen test, bot se nemění. Skript `scratch/f25_pary.py`.

## Plán (zapsán PŘED výpočtem)
**Dvojice:** NAS100/SPX500, XAU/XAG, EURUSD/GBPUSD. Brent/WTI slouží jako jiný trh.

**Pravidlo (H1 zavírací ceny):**
- **Spread:** s = ln A − β · ln B. β je sklon OLS za posledních 1 400 svíček H1 (asi 60 dní).
- **z-skóre:** z = (s − průměr) / směrodatná odchylka za posledních 460 svíček (asi 20 dní). Vše jen z minulých dat.
- **Vstup** na otevření další svíčky, jedna pozice na dvojici:
  - z > +2 → short spread (short A, long β·B);
  - z < −2 → long spread.
- **Výstup** na otevření další svíčky:
  - z se vrátí přes 0;
  - stop při |z| ≥ 4;
  - nejdéle 230 svíček (asi 10 dní).
- **Výsledek:** výnos A − β · výnos B (v % nominálu nohy A).
- **Náklady:** spread brokera podle hodiny a tick na obou nohách, swap obou nohou za každou noc (ze středy na čtvrtek 3×).
- **R:** výsledek / (2 · směrodatná odchylka spreadu při vstupu), tedy asi ztráta při stopu.

**Data:**
- **Vývoj:** NAS/SPX HistData (M1 → H1) do 2019-02-20; XAU/XAG a EUR/GBP broker H1 do 2018-12-31.
- **Kontrola:** broker od 2019 (NAS/SPX z M1, ostatní H1).
- **Druhý zdroj:** NAS/SPX HistData 2019–2025.
- **Jiný trh:** Brent/WTI broker 2019–2026.

**Náhoda:** stejná dvojice, náhodná svíčka ve stejném období, stejný směr a stejná doba držení, stejné náklady.

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. Vývoj (všechny tři dvojice dohromady) > 0 a t ≥ 2,0.
2. Kontrola > 0 a t ≥ 1,5.
3. Brent/WTI > 0.
4. Lepší než náhoda ve vývoji i v kontrole.
5. Druhý zdroj > 0.

## Výsledky (2026-11-07)
Souhrn je v `research_data/f25/f25_souhrn.txt`.

| Část | Dvojice | n | R/obchod | t | % na obchod po nákladech | bez nákladů |
|---|---|---|---|---|---|---|
| Vývoj | NAS/SPX (HistData) | 103 | +0,003 | 0,63 | +0,08 % | +0,20 % |
| | XAU/XAG | 121 | +0,040 | 1,60 | +0,28 % | +0,47 % |
| | EUR/GBP | 117 | +0,009 | 0,22 | −0,06 % | +0,01 % |
| | **celkem** | 341 | **+0,018** | **1,13** | | |
| Kontrola | NAS/SPX (broker) | 81 | −0,009 | −1,22 | −0,34 % | −0,20 % |
| | XAU/XAG | 92 | +0,022 | 1,05 | −0,09 % | +0,06 % |
| | EUR/GBP | 102 | +0,002 | 0,03 | +0,04 % | +0,12 % |
| | **celkem** | 275 | **+0,006** | **0,20** | | |
| Druhý zdroj | NAS/SPX HistData 2019–25 | 80 | +0,005 | 0,40 | −0,12 % | |
| Jiný trh | Brent/WTI | 74 | +0,012 | 0,30 | +0,88 % | |

- Náhoda (stejný směr a doba držení): vývoj −0,016 R, kontrola −0,024 R. To jsou jen náklady.
- **Spread se za 10 dní většinou nevrátí:** 75–78 % obchodů končí časovým stopem (230 h).
  - Z-skóre 2 neoznačuje „přetažení“, které se rychle vrací. Dvojice se spíš trvale rozjíždějí.
- Po letech kolísá kolem nuly: nejlepší 2016–17 a 2024, nejhorší 2025 (−4,1 R).

## Rozhodnutí podle pravidel zapsaných předem
1. Vývoj > 0 a t ≥ 2,0: **NE** (t 1,13).
2. Kontrola > 0 a t ≥ 1,5: **NE** (t 0,20).
3. Brent/WTI > 0: ANO (+0,012).
4. Lepší než náhoda: ANO.
5. Druhý zdroj > 0: ANO (+0,005).

**⇒ BEZ VÝHODY.** Je to lepší než náhodné vstupy, ale výsledek se drží u nuly a statisticky nic neukazuje.

**Co si vezmeme:**
- Dvojice NAS/SPX, XAU/XAG a EUR/GBP se na H1 do 10 dní k průměru nevracejí.
- Strategie na stejné straně obou trhů z dvojice (např. průraz na NAS i SPX zároveň) v botovi **zdvojují riziko**. Korelace drží dlouhodobě, odchylky se nevracejí rychle, ale ani se nepřevracejí.
- Pokud se někdy k párům vrátíme, tak spíš na denních datech s delším oknem. Nové hledání by ale potřebovalo nový plán předem.
