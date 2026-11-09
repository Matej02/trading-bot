---
tags: [vyzkum, f33, kalendar, mesicni]
datum: 2026-11-08
---
# F33 Rebalancování na konci měsíce

Z [[Fronta nápadů F22–F33|fronty nápadů]]. Jen test, bot se nemění. Skript `scratch/f33_rebal.py`.

**Data:** Yahoo TLT, IEF a SPY (upravené ceny včetně dividend) 2003–2026 v `research_data/f33/yahoo`, staženo se souhlasem uživatele 2026-11-08.

## Plán (zapsán PŘED výpočtem)
**Pravidlo** (Harvey a kol.: fondy 60/40 na konci měsíce prodávají, co vyrostlo):
- **Signál** na zavření 4. obchodního dne od konce měsíce (L−3): rozdíl = výnos SPY − výnos TLT od posledního zavření předchozího měsíce.
- **Obchod jen při |rozdíl| ≥ 2 procentní body:**
  - akcie předběhly dluhopisy → **short** indexů;
  - dluhopisy předběhly akcie → **long**.
- **Vstup** na otevření dne L−2, **výstup** na zavření posledního obchodního dne měsíce L (3 dny).
- **Náklady:** půl spreadu brokera na vstupu i výstupu, swap za noci.
- **R** = výsledek / ATR20 denního rozpětí indexu, bez stopu.
- **Hodnotí se po měsících** (průměr SPX500 a NAS100), ne po obchodech. Poučení z [[F31 Drift před FOMC|F31]].

**Data:**
- **Vývoj:** Yahoo 2003–2018.
- **Kontrola:** Yahoo 2019–2026.
- **Druhý zdroj:** H1 brokera → denní 2019–2026 (signál z ETF).
- **Jiné trhy:** US30 a DAX (Yahoo, celé období).

**Srovnání:** stále long ve stejných dnech, na konci měsíce bývá růst (turn-of-month).

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. Vývoj > 0 a t ≥ 2,0.
2. Kontrola > 0 a t ≥ 1,5.
3. US30 i DAX > 0.
4. Lepší než stále long ve stejných dnech, ve vývoji i v kontrole.
5. Druhý zdroj > 0.

## Výsledky (2026-11-08)
- Souhrn: `research_data/f33/f33_souhrn.txt`.
- Signál padl ve 201 z 286 měsíců (126× short, 75× long), tedy asi 8× ročně.

**Po měsících (průměr SPX500 a NAS100):**

| Část | Měsíců | R | t | výhra | stále long stejné dny |
|---|---|---|---|---|---|
| Vývoj 2003–2018 | 137 | **+0,305** | **3,21** | 60 % | +0,009 |
| Kontrola 2019–2026 | 63 | **+0,230** | **1,57** | 56 % | −0,047 |
| Druhý zdroj (broker) 2019+ | 55 | +0,193 | 1,26 | 53 % | −0,094 |
| US30 (celé období) | 200 | +0,345 | 4,34 | 64 % | −0,040 |
| DAX (celé období) | 200 | +0,220 | 2,75 | 60 % | +0,022 |

- **Vydělávají oba směry:**
  - vývoj: short +0,235 R, long +0,408 R;
  - kontrola: short +0,179 R, long +0,357 R.
- **Po letech kladné 21 z 24 let.** Ztrátové 2010, 2020 a 2023.

## Rozhodnutí podle pravidel zapsaných předem
**Všech 5 bodů ANO → VÝHODA.** Hodnoceno po měsících, tedy už s opravou z [[F31 Drift před FOMC|F31]].

**Kontrola odolnosti (popisně, pravidla se nemění):**
- Práh 0 / 1 / 2 / 3 p. b. × poslední 2 / 3 / 4 dny:
  - vývoj kladný ve všech 12 variantách (t 1,99–4,34);
  - kontrola kladná v 11 z 12, ale t ≥ 1,5 jen ve 3 (plánovaná mezi nimi).
- Bez 5 nejlepších měsíců +0,212 R (t 2,82), bez 10 nejlepších +0,156 R (t 2,14).
- Odpovídá to literatuře (Harvey, Mazzoleni a Melone): kladný efekt je i na trzích, na kterých se nic nevybíralo (US30, DAX).

**⇒ NEJSILNĚJŠÍ VÝSLEDEK ZE VŠECH TESTŮ.** V kontrole 2019–2026 je ale slabší a citlivější na nastavení.
- **Prakticky:** asi 8 obchodů ročně na US indexech. Vstup na otevření L−2 (15:30 Praha), výstup na zavření posledního dne měsíce (22:00 Praha, s PC do 20:00 nejde). Výstup 19:45 by vyžadoval nový test.
- **Do bota zatím ne** (přání uživatele). Návrh: sledovat dopředu beze změn pravidel a vyhodnotit po 12 měsících.

## Live v simulátoru (od 2026-11-09, build db85757)
- Systém `f33_rebal_d1` v `simulator/lib/f2x.ts`, kontrola shody `scripts/compare-f2x.ts` (200/200 signálů, den i směr).
- **Odchylky od testu:** vstup na zavření dne L−3 (v testu otevření L−2), ceny SPY/TLT z Yahoo bez dividend (v testu upravené), SL 3 ATR jako pojistka (v testu bez stopu). Trhy SPX500 a NAS100.
- V registru Statistika: **validated (PF 1,89, n 200 měsíců)**.
