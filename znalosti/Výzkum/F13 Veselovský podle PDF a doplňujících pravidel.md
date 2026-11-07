---
tags: [vyzkum, f13, fm]
datum: 2026-11-03
---
# F13 – Veselovský: PDF a obrázky jako zdroj, doplňující pravidla jako dodatek

Zadání uživatele (3. 11.): Word s [[Doplňující pravidla k FM PDF|doplňujícími pravidly]] je jen dodatek. Hlavní zdroj jsou PDF.
Projít vše, pak testovat a dát živě.

Prošel jsem:
- celý text 32 PDF;
- všech **49 obrázků** [[FM obrázky – Michal Veselovský (day)|galerie]];
- Základy Likvidita, Volume a Price Action (viz [[F12 Můčka podle doplňujících pravidel|F12]]);
- z Wordu bod B2.

Plán předem je v `F13_PLAN.md`, kód v `research_f13_ves.py` a `research_f13_eval.py`, výstupy v `research_data/f13/`.

## Pravidla v testu (zdroj)
- **Daily bias** [PDF Daily bias]:
  - close nad PDH → bullish;
  - sweep PDH a close pod → bearish (zrcadlově u PDL);
  - close ve wicku: nad/pod 50 %;
  - close v těle předchozí svíčky = range, neobchoduje.
  - Po trefení cíle biasu je den hotový [PDF Trading plán; B2].
- **Killzones** [PDF]: Londýn 8–11 (long do 11:30) a NY 14–17 pražského času. Bez FOMC, NFP a CPI.
- **Sweep** Asie (2–8), PDL/PDH nebo 15m swingu, poprvé touto nohou, **pod NY daily open** (6:00) pro long [PDF PO3, Entry model; obr 40–42, 47].
- **MSS** na 1m/5m: close tělem s momentem za strong levelem (stroj z F12) a FVG v noze (displacement) [PDF Entry model, obr 46].
- **Důležitá úroveň** – tři varianty:
  - jen sweep likvidity;
  - H1/15m zóna (OB, FVG, iFVG, BPR);
  - OB podle B2 (jen těla, platný po close, na likviditě nebo FVG, s HVN).
- **Vstup limitem:** první FVG s 0,382, golden pocket 0,618, nebo 50 % OB z nohy MSS [PDF Shrnutí, OB praxe, obr 23–26].
- **SL** 2 pipy za sweep, nejvýš 15 pipů (jinde 0,21 ATR D1).
- **TP:**
  - TP1 = opačná strana Asie (50 %) + BE, TP2 = cíl biasu (PDH/PDL); nebo vše na TP2;
  - RR k cíli ≥ 2 [PDF Management pozic, obr 40].
- **Max 2 SL denně.**

## Výsledky (s náklady, vývoj do 2021, OOS 2022–26)
- 36 variant × 5 trhů, 12 499 obchodů.
- **Vybraná na vývoji:** `1m, úroveň = sweep LQ, vstup 50 % OB, TP1 Asie + TP2 cíl biasu`:
  - vývoj **−0,06 R** (n 375), OOS **+0,07 R** (n 388), PF 1,10;
  - náhoda se stejným SL/TP, časem a směrem: −0,14 / −0,08 R;
  - bez nákladů +0,10 / +0,10 R, náhoda bez nákladů −0,19 R.
- **Prahy na všech trzích nesplnila.**

| Trh | vývoj | OOS |
|---|---|---|
| EURUSD | −0,17 R (106) | −0,12 R (48) |
| GBPUSD | −0,09 R (57) | −0,19 R (43) |
| XAUUSD | −0,33 R (91) | −0,02 R (103) |
| **NAS100** | **+0,23 R (60)** | **+0,22 R (100)** |
| **SPX500** | **+0,28 R (61)** | **+0,24 R (94)** |

**Vrstvy:**
- **Daily bias pomáhá v obou obdobích:**
  - s biasem vývoj −0,06 R, OOS +0,07 R;
  - bez biasu −0,17 R a −0,03 R při 3× více obchodech.
  - Je to první koncept z FM, který konzistentně přidal.
- NY DO přidá málo (bez něj −0,09 / +0,05 R).
- Zóny navíc ke sweepu nic nemění.
- Vstup 50 % OB je lepší než FVG a GP.

**Indexy NAS100 + SPX500** jsou předem v testu kvůli B2 („funguje líp na indexech, S&P a NQ korelují“), nevybral jsem je až podle výsledku:
- vývoj **+0,26 R** (n 121, PF 1,39), OOS **+0,23 R** (n 194, PF 1,31);
- náhoda −0,02 / +0,07 R;
- shorty +0,30 R a longy +0,16 R, takže to není jen růst indexů;
- roky: 2019 +0,03, 2020 +0,23, 2021 +0,42, 2022 +0,35, **2023 −0,51**, 2024 +0,57, 2025 +0,59, 2026 −0,46.
- **Slabiny:**
  - výhra jen 27–34 %, medián cíle 6,4 R; bez 5 nejlepších obchodů zbude +0,09 R;
  - na indexech mimo test je to smíšené: US30 vývoj +0,54 R, OOS −0,03 R (náhoda −0,10 R); DAX vývoj +0,44 R, OOS −0,27 R.

![[F13 Veselovský – ukázky obchodů SPX500 (OOS).png]]
![[F13 Veselovský – ukázky obchodů EURUSD (OOS).png]]

## Live (simulátor, 2026-11-03)
- Systém `fm13_ves_m1` (`lib/fm13.ts`) na trzích NAS100fut, SPX500fut, EURUSD, GBPUSD, XAUUSD.
  - Indexy NAS100fut a SPX500fut jsou nové datové zdroje z futures NQ=F a ES=F (23 h), `feedOnly`, takže je momentum neobchoduje.
- **Rozdíly proti testu:**
  - Celý TP jde na cíl biasu (simulátor neumí částečné výstupy). V testu to je varianta `tp2`.
  - Vstup je trhem na 1m svíčce, která 50 % OB zasáhne.
  - Bez podmínky objemu v MSS, protože Yahoo u forexu objem nedává. Test bez objemu: indexy `tp2` vývoj +0,10 R (n 141), OOS +0,22 R (n 227).
  - Zprávy hlídá agent Kalendář místo vynechání dnů FOMC, NFP a CPI.
  - Limit 2 SL denně hlídá jen denní limit Risku.

## Závěr
- **Nejlepší výsledek ze všech FM strategií, ale ne ověřená výhoda.**
- Na US indexech (NAS100, SPX500) je OOS kladný a nad náhodou a daily bias funguje v obou obdobích.
- Výsledek ale stojí na vzácných velkých výhrách (cíl PDH/PDL) a na US30 a DAX se v OOS neopakuje.
- Forex a zlato jsou bez výhody.
- **Ověření na delší historii (2026-11-07): NEPROŠLO.** Na nových letech 2010–2019 −0,11 R (n 417), celek t 0,42, viz [[F13 indexy na delší historii (HistData 2010–2025)|F13 na delší historii]].
- **Kandidát na live test na NAS100 a SPX500** (živě je potřeba 24h data, Yahoo `^NDX` má jen hodiny burzy → futures NQ=F/ES=F).
