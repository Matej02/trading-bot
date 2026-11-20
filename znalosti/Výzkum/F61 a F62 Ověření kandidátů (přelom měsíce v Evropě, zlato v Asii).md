---
tags: [vyzkum, f61, f62, kalendar, zlato, overeni]
datum: 2026-11-20
---
# F61 a F62 Ověření dvou kandidátů

Zadání uživatele (2026-11-20): „Koukni na ty 2 kandidáty a klidně stáhni.“ Souhlas se stažením Yahoo GLD, IAU, SLV (denní) a GC=F (hodinové). Bot ani simulátor se nemění.

## F61 Přelom měsíce v Evropě (kandidát A z [[Souhrn testů F55–F60 (2026-11-20)|F55]])
**Proč:** v F55 vyšel DAX a FTSE jako „jiné trhy“ s převisem t 2,7. Je to zjištění po výpočtu, proto se ověřuje jen na tom, co jsme ještě **nepočítali**: EuroStoxx 50 a IBEX (Yahoo) a data brokera.

### Plán (zapsán PŘED výpočtem)
- **Pravidlo stejné jako F55:**
  - long na otevření posledního obchodního dne měsíce, ven na zavření 3. obchodního dne dalšího;
  - R / ATR20, náklady půl spreadu + swap;
  - srovnání = stejné 4denní okno v ostatních dnech.
- **ANO (= kandidát na sledování v simulátoru) jen když platí vše:**
  1. EuroStoxx + IBEX (Yahoo, celé období): signál > 0, převis > 0, t ≥ 2,0.
  2. EuroStoxx + IBEX 2019–2026: signál > 0 a převis > 0.
  3. Broker 2019–2026 (DAX, FTSE, CAC, EuroStoxx, IBEX): signál > 0 a převis > 0.
  4. Převis kladný aspoň v 55 % let (DAX, FTSE, EuroStoxx, IBEX, Yahoo).
- I při ANO jen sledování dopředu, protože nápad vznikl až po výpočtu.
- **Popis:** DAX + FTSE zvlášť do 2018 a od 2019.

## F62 Druhý zdroj pro F46 zlato v Asii (kandidát B)
**Proč:** [[F46 a F47 Zlato a dluhopisy|F46]] stojí jen na datech brokera.

### Plán (zapsán PŘED výpočtem)
**B1, ETF GLD (Yahoo, od 2004):**
- Noc = zavření (t−1) → otevření (t), den = otevření (t) → zavření (t), obojí v ATR20.
- Hypotéza: zlato vydělává mimo americkou seanci, v ní ne. Převis = noc − den, Welch t.
- Noc GLD (16:00 → 9:30 NY) obsahuje asijskou seanci i londýnské dopoledne, je to tedy širší okno než F46.
- **Podmínky:**
  1. Vývoj 2004–2018: noc > 0, převis > 0, t ≥ 2,0. Roky 2004–2008 jsou pro F46 úplně nová data.
  2. Kontrola 2019–2026: noc > 0, převis > 0, t ≥ 1,5.
  3. IAU (jiný fond na zlato): převis > 0.
  4. Převis kladný aspoň v 55 % let.
- Popis: SLV (stříbro), v F46 se neopakovalo.

**B2, futures GC=F (Yahoo hodinové, jen poslední ~2 roky):**
- Přesně pravidlo F46: long 23:00 → 07:00 Londýn, náklady spread brokera XAU.
- Srovnání: stejné 8h okno se začátkem v ostatních hodinách 0–22.
- **Podmínka 5:** signál > 0 a převis > 0. Popis: shoda s brokerem ve stejných dnech (korelace denních R).

**F46 má potvrzený druhý zdroj, jen když platí 1–5.** Pravidla F46 ani její verdikt (bod 4 o vlásek NE) se dodatečně nemění. Výsledek jen zvyšuje nebo snižuje důvěru při sledování dopředu.

Skripty `scratch/f61_f62.py`, `scratch/f62_stahni.py`, výstup `research_data/f61/souhrn.txt`.

## Výsledky (2026-11-20)
Souhrn `research_data/f61/souhrn.txt`.

### F61 Přelom měsíce v Evropě: NEPROŠLO (o vlásek)
| Část | Signál R | Převis | t |
|---|---|---|---|
| EuroStoxx + IBEX, celé období (nové trhy) | +0,164 | +0,152 | **1,92** (laťka 2,0) |
| EuroStoxx + IBEX 2019+ | +0,169 | +0,132 | 0,75 |
| Broker 2019+, 5 trhů | +0,248 | +0,230 | 1,17 |
| Popis: DAX + FTSE do 2018 / od 2019 | +0,235 / +0,207 | +0,235 / +0,181 | 2,95 / 1,10 |

- Všech 5 trhů u brokera kladných, převis kladný v 62 % let.
- Rozhoduje bod 1: t 1,92 < 2,0 ⇒ **NEPROŠLO**. Yahoo EuroStoxx má krátkou historii (233 obchodů) a vyšel kolem nuly, IBEX t 1,76.
- **Hodnocení:** směr všude správný a velikost stálá i od 2019. Je to nejlepší „téměř“ kandidát vedle F46. Podle pravidla uživatele může jít jen do simulátoru na sledování dopředu, a to jen s jeho souhlasem.

### F62 Druhý zdroj pro F46: NEPOTVRDIL
| Část | Výsledek |
|---|---|
| GLD 2004–2018, noc − den | +0,015 ATR, t 1,13 (**NE**) |
| GLD 2019–2026, noc − den | +0,055, t 2,92 |
| IAU / SLV celé | +0,043 t 3,88 / +0,034 t 2,97 |
| Roky GLD | 70 % kladných |
| **GC=F 1h, přesné pravidlo F46, 11/2024–10/2026** | +0,003 R, převis −0,003 (**NE**) |

- **Důležité zjištění o datech brokera:**
  - od 2022 chybí v datech brokera v létě svíčka 23:00 Londýn. Test F46 tak v kontrole 2022–2026 obsahoval skoro jen zimní dny (2022: 104 dní, 1 letní);
  - celé období brokera: zimní dny +0,030 R, letní +0,001 R;
  - GC=F posledních 2 let: zima +0,009, léto −0,002.
  - Hodinové ceny brokera se proti futures v některých hodinách systematicky liší o ~1 $, například zavření 06:00 +1,35 $. Vypadá to na posun o hodinu v části roku. To zvýhodňuje výstup F46 asi o 0,02 R, tedy zhruba o celou naměřenou výhodu.
- **Závěr:**
  - jev „drahé kovy rostou mimo americkou seanci“ v ETF existuje, hlavně od 2019;
  - **přesné okno F46 se na nezávislých hodinových datech nepotvrdilo** a výsledek brokera může být částečně artefakt času a výběru dní;
  - F46 v simulátoru se nechává jen jako sledování dopředu, se sníženou důvěrou;
  - na MT5 ne.
