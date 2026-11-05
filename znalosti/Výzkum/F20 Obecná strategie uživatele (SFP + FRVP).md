---
tags: [vyzkum, f20, uzivatel, smc, volume]
datum: 2026-11-04
---
# F20 – obecná strategie uživatele: top-down + SFP s FRVP

Zdroj: vlastní pravidla uživatele, [[Doplňující pravidla k FM PDF]] část A1–A8.

**Před testem prošlé celé Základy, text i všechny obrázky:**
- [[FM obrázky – Základy – Volume|Volume (49 obr.)]]
- [[FM obrázky – Základy – Likvidita|Likvidita (12)]]
- [[FM obrázky – Základy – Price Action|Price Action (32)]]
- [[FM obrázky – Základy – Supply a Demand|S&D (136)]]

Plán s odkazy na lekce: `F20_PLAN.md`. Kód: `research_f20_user.py`, vyhodnocení `research_f20_eval.py`.

## Pravidla
- **Bias:** hlavní 4H struktura (BOS ≤ 30 dní) [A2, A8]. Varianta s 15m strukturou stejným směrem (≤ 5 dní).
- **POI:** knot sáhne do aktivní S/D zóny 4H/15m (pravidlo 25 %) [A4] nebo na POC předchozího dne [A8].
- **SFP v 15m svíčce** [A6]:
  - knot za nevybraným 15m swingem (pivot ±5, nejvýš 2 dny);
  - tělo se zavře zpět.
- **FRVP do svíčky** [A6, A7]:
  - 250 řádků, VA 70 %, z M1 svíček uvnitř 15m;
  - POC/VAH/VAL v knotu 2 ze 3 nebo 3 ze 3.
- **Objem** svíčky nad SMA 50 [Likvidita s Volume s7, obr. Likvidita 3–8: „jedná se / nejedná se o výběr LQ“].
- **Čas:** 9:00–20:00 Praha, bez vstupů kolem FOMC/NFP/CPI. Konec ve 22:00.
- **Vstup:** po zavření svíčky / po 1m MSS / limitem na POC svíčky.
- **SL** za knot + 0,1 ATR15, aspoň 3× spread.
- **TP:** 2R / opačný 15m swing / nahý denní POC (magnet [A4, Volume nPOC]).

![[F20 obecná strategie – ukázky obchodů (OOS).png]]

## Výsledek
7 trhů: EURUSD, GBPUSD, USDJPY, XAUUSD, NAS100, SPX500, DAX. M1 data, náklady brokera, 486 variant.

**Vybraná na vývoji** (bias 4H + 15m, zóna, FRVP ≥ 2/3, vstup po zavření, TP nahý POC):

| | Vývoj ≤ 2021 | OOS 2022–26 |
|---|---|---|
| Strategie | +0,28 R (n 32) | **+0,78 R** (n 27), PF 2,4 |
| Náhoda se stejným SL/TP | −0,30 R | +0,05 R |

- Na OOS t = 1,8, bootstrap P(průměr ≤ 0) ≈ 4 % (bez korekce na výběr ze 486 variant).
- Bez nákladů: vývoj +0,29 R, OOS +0,95 R.

**Rodina 8 sousedních variant** (bias 4H/4H+15m × zóna/zóna+POC × FRVP 0/2, vstup po zavření, TP POC):
- všech 8 je na OOS kladných (+0,06 až +0,78 R);
- na vývoji jsou skoro všechny záporné, unikátní obchody −0,21 R (n 194) vs OOS +0,11 R (n 166).

**Jádro bez filtrů nemá výhodu:**
- SFP + FRVP 3/3 bez dalších filtrů, bez nákladů: −0,04 R (n 2 100), stejně jako SFP v [[F7 Dokument 6 strategií SMC|F7]];
- všechny varianty bez nákladů: vývoj −0,07, OOS −0,03 R.

**Filtry (průměr přes varianty):**
- FRVP v knotu: 2/3 lehce lepší na OOS (−0,13 vs −0,15 R), 3/3 nepomáhá.
- Objem nad SMA 50: má ho 93 % SFP, takže nic nefiltruje.
- Zóna a 15m bias pomáhají jen na OOS, na vývoji ne.

**Náklady:** u EURUSD je SL za knotem u 49 % SFP blíž než 3× spread brokera (1,9 pipu), takže tyhle obchody vypadnou.

![[F20 obecná strategie – kumulativní R.png]]

Vybraná varianta vydělala hlavně 2021–2023, od 2023 je plochá. 2025–26 kolem nuly.

## Závěr
**NEOVĚŘENO, slabý náznak** podobně jako [[F13 Veselovský podle PDF a doplňujících pravidel|F13]]:
- Kombinace 4H/15m bias + S/D zóna + SFP + cíl na nahém denním POC vychází kladně na OOS u celé rodiny variant a je lepší než náhoda.
- Jenže na vývoji kladná není (kromě vybrané varianty), obchodů je jen asi 5 za rok na 7 trzích a poslední 2 roky jsou ploché.
- Samotné SFP + FRVP výhodu nemá. Případná výhoda je v kontextu (směr, zóna) a v cíli na POC.

## Live
Od 2026-11-04 běží jako `F20_user` (magic 20261120) na MT5 demu v [[FM live test na MT5 demu|runneru]].
- **Shoda** kandidátů SFP a filtrů ze živých dat MT5 s historií:
  - EURUSD 51/51, GBPUSD 221/221, SPX500 288/288, NAS100 236/236, DAX 114/114, zlato 86/86;
  - USDJPY 186/198;
  - vybrané signály 18/18.
- **Potřebuje 180 dní M1 historie:** se 75 dny se 4H stav na SPX500 lišil (36/50 → se 180 dny 50/50).
- **Do simulátoru na Vercelu není dán:** Yahoo 1m data jsou jen 5 dní, chybí 4H struktura z M1 i FRVP svíčky.
