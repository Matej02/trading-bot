# F13 – Veselovský: PDF + obrázky jako zdroj, doplňující pravidla (B2) jako dodatek (plán předem, 2026-11-03)

Zdroje:
- celý text 32 PDF (`scratch/fm/veselovsky_vse.txt`);
- všech 49 obrázků (`znalosti/FM/Obrázky/FM obrázky – Michal Veselovský (day).md`, číslo = [obr N]);
- Základy: Likvidita, Volume/SVP, Price Action (prohlédnuto u F12);
- Word B2 jen tam, kde PDF mlčí.

## Pravidla (odkaz na zdroj)
1. **Daily bias** [PDF Daily bias, obr 2, Likvidita praxe obr 16–20]:
   - close tělem nad PDH → bullish (cíl další high);
   - sweep PDH a close pod → bearish (cíl PDL), zrcadlově u PDL;
   - close ve wicku předchozí svíčky: nad 50 % wicku bullish, pod 50 % bearish;
   - close uvnitř těla předchozí svíčky = range → neobchoduje.
   Obchod jen ve směru biasu. Po trefení cíle (externí likvidity) se v ten den už nevstupuje [PDF Trading plán; B2 „když se vybírá externí likvidita, neobchoduje“].
2. **Čas** [PDF Killzones, Trading plán] (pražský čas):
   - Londýn 8–11, long ještě do 11:30;
   - NY 14–17, od 13:00, pokud ve 14:30 nejsou red news (red news v datech nemáme, pevně 14:00).
   - Asie 2–8 = akumulace (Asia H/L).
   - Neobchoduje dny FOMC, NFP a CPI; PPI a PMI v datech nemáme.
3. **Likvidita a manipulace** [PDF Likvidita ERL/IRL, PO3, obr 21, 40–42, 48–49]:
   - sweep Asia low / PDL / posledního 15m swing low (long);
   - **pod NY daily open** (open v 0:00 NY = 6:00 Praha) pro long, nad ním pro short [PDF Entry model, obr 47].
   - Bez sweepu se nevstupuje.
4. **MSS** [PDF Entry model, obr 46]: na 1m nebo 5m close tělem s momentem za low/high, které tvořilo BOS
   (stejný stroj jako F12 – změna struktury přes strong level), s displacementem = FVG v noze. MSS knotem nestačí.
5. **Důležitá úroveň** (varianta) [PDF Entry model „jinde bezcenný“, Shrnutí, Timeframes breakdown]:
   - `liq`: stačí sweep likvidity (jako F11);
   - `zona`: sweep extrém navíc v H1/15m zóně ve směru obchodu (OB, FVG, iFVG, BPR);
   - `obhvn`: v OB podle B2 – řada svíček opačné barvy jen těly [PDF OB praxe „skupina jen těly“; B2], platný až po close
     za zónou, s FVG v impulzu, OB na HVN (tick volume za 24 h) [B2, PDF SVP].
6. **Vstup limitem** (varianta) [PDF Shrnutí, Entry model, OB praxe, obr 23–26, 40]:
   - `fvg`: první FVG v noze MSS, proximal hrana („první FVG s 0,382“);
   - `gp`: 0,618 nohy sweep → extrém po MSS;
   - `ob50`: 50 % těl OB v noze MSS.
   Limit platí do konce killzone.
7. **SL** ±2 pipy za extrém sweepu [PDF Shrnutí, Trading plán]. SL 5–10 pipů je jeho norma, nad 15 pipů (jinde 0,21 ATR D1) se neobchoduje.
8. **TP** (varianta) [PDF Management pozic, obr 40]:
   - `tp12`: TP1 = opačná strana Asie (50 %) a pak BE, TP2 = cíl biasu (PDH/PDL);
   - `tp2`: vše na cíli biasu.
   RR k cíli biasu ≥ 2 [PDF OB teorie „min 1:2“]. Zavřít do 22:00.
9. **Max 2 SL denně**, riziko stejné [PDF Daily SL].

## Trhy a vyhodnocení
- EURUSD (hlavní), GBPUSD, XAUUSD [PDF Úvod: „primárně EURUSD, jde i jiný forex a zlato“].
- NAS100, SPX500 [B2: „funguje líp na indexech, S&P a NQ korelují“].
- Mřížka 2 (1m/5m) × 3 (úroveň) × 3 (vstup) × 2 (TP) = 36 variant. Výběr jen na vývoji (do 2021), OOS 2022–26.
- Kontroly: náhoda (stejné SL/TP, čas, směr), bez nákladů, vrstvy (bias / NY DO / zóna).
- Prahy: n ≥ 100, exp ≥ 0,15 R, PF ≥ 1,3, o 0,1 R nad náhodou.

## Předpoklady (z materiálu nejdou přesně)
- velikost swingu MSS (k = 1,5 ATR, jako F12);
- „momentum“ = tělo ≥ průměr 20 těl;
- HVN = koš s objemem ≥ 1,5× medián profilu;
- BPR jen z překryvu dvou aktivních FVG opačného směru;
- 13:00 bez news se nepoužije (red news nemáme).
