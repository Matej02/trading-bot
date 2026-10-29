---
tags: [vyzkum, f8, fm]
datum: 2026-10-29
---
# F8 – strategie z FM PDF (S/D zóny na vyšších TF, daily bias, makro skóre)

Zadání uživatele: backtestovat koncepty a strategie z [[FM materiály|FM PDF]], hlavně hledání S/D zón na vyšších TF podle mentorů.
Plán byl sepsaný předem v `F8_PLAN.md`. Skripty: `research_f8.py`, `research_f8_eval.py`, `research_f8_kontrola.py`, `research_f8_score.py`.
Výstupy jsou v `research_data/f8/`.

## Data a metodika
- MT5 H1 2009–2026 (indexy od 2019), z nich H4, D1 a W1. Den končí v 17:00 NY.
- 26 trhů: 15 forex, zlato a stříbro, 7 indexů, 2 ropy. Náklady brokera (spread podle hodiny, swapy) → [[Náklady brokera]].
- Simulace `sim_trade` z F7: limit se vyplní až průchodem o 1 tick, SL a TP ve stejné svíčce = SL.
- Vývoj do 2019, OOS od 2020, srovnání s [[Náhodné vstupy|náhodnými vstupy]] → [[Výběr, kontrola, holdout]].

## Test A – S/D zóny podle FM → [[Supply a demand zóny]]
**Pravidla zóny:**
- Báze 1–6 malých svíček (tělo ≤ 0,5 ATR).
- Pohyb ven 1–3 svíčky ≥ 1,5 nebo 2 ATR, první tělo ≥ 0,5 ATR.
- Do 5 svíček **BOS** (close za posledním swingem).
- Proximal = nejvyšší tělo báze, distal = extrém knotu.
- **Jen první dotek**, limit na proximal, SL za distal.

**Varianty** (192 na test):
- pivotní / všechny zóny;
- trendový filtr (2 vyšší high a 2 vyšší low);
- SL +20 % (Hvězda);
- TP 2R / 3R / protější zóna;
- BE při 1R.

**Testy:** A1 = D1 zóny (Šrajer swing), A2 = D1 zóna uvnitř W1 zóny (Hvězda), A3 = H4 zóny (Šrajer DT, Valchář).

| Test | Vybraná varianta (na vývoji) | DEV | OOS 2020–26 | Náhoda OOS |
|---|---|---|---|---|
| A1 D1 | k2 vše sl20 TP zóna BE | −0,01 R (n 214) | **−0,22 R** (n 255), kvartály 32 % | −0,07 R |
| A2 D v W | – | žádná varianta n ≥ 100 (2–10 obchodů) | – | – |
| A3 H4 | k2 vše trend TP 2R BE | −0,01 R (n 181) | **−0,17 R** (n 153), kvartály 27 % | −0,04 R |

**Plato:** medián OOS přes všechny varianty −0,19 R (D1) a −0,12 R (H4). Kladných je jen 12–19 % variant. Žádná varianta neprošla prahy.
Zóny na vyšším TF tedy nefungují o nic líp než na 1h ([[F5 SMC a volume profile na 1h|F5]]) nebo M1–M15 ([[F7 Dokument 6 strategií SMC|F7]]).

**Chyba nalezená kontrolou (poučení → [[Metodické pasti]]):**
- První běh ukázal H4 +0,54 R OOS, ziskových 85 % kvartálů. Byl to **pohled do budoucnosti**.
- Zóna se aktivovala po první svíčce pohybu ven, ale kvalifikovala se i podle dalších 1–2 svíček, které ještě nebyly známé.
- Prozradil to test s vstupem o 4 h později (výsledek −0,04 R).
- Po opravě (zóna platí až po dokončení pohybu ven) výhoda zmizela.

## Test B – Daily bias → [[Daily bias]]
- Pravidla Veselovského (close nad PDH → nahoru, sweep a návrat → opačně) a Můčky (směr předchozí svíčky).
- **Zásah cíle 62–65 %**, u opačného směru 29–31 %.
- Míra je nafouknutá blízkostí cíle: po býčí svíčce je PDH hned u open, průměrný cíl je jen 0,35 R.
- **Obchod open → cíl, SL opačný PD extrém, výstup na konci dne: −0,06 R** (V i M, DEV i OOS, n 32–43 tisíc). Opačný směr dává −0,16 až −0,19 R.
- Pravidlo tedy má **slabý směrový náklon** (o ~0,12 R lepší než opačný směr), ale samo se obchodovat nedá. Může sloužit nanejvýš jako filtr.

## Test C – Makro skóre (Trading Analyzer, CSV 2017–2024) → [[Makro skóre měn]]
- **Změna skóre o ≥ 2 body:** výnos za 5, 10 a 20 dní je −0,07 až +0,03 ATR po spreadu, zásah 48–50 %, v DEV i OOS. Žádná výhoda.
- **Bias |skóre| ≥ 5:** DEV +0,017 ATR za den, OOS +0,004 ATR za den (Sharpe ~0). Žádná výhoda.
- Tvrzení FM, že „změny skóre fungují perfektně“ a „cena následuje skóre“, data nepotvrzují.

## Závěr
**Nic z FM strategií testovaných v F8 nemá doloženou výhodu, takže se do bota nic nenasazuje.**
- S/D zóny po FM jsme teď testovali na všech TF (M1 až W1) a nefungují nikde.
- Live test v simulátoru nemá smysl: backtest na 17 letech a 26 trzích je jednoznačně záporný.

**Co z FM zatím netestováno:**
- intraday ICT model Veselovského s daily bias filtrem (M1/M5);
- Kimmel na US100/US500;
- Pátkovy průrazy NQ M5;
- svíčkové potvrzení v zóně (Hvězda: hammer, engulfing);
- objemové potvrzení s futures daty (nemáme).
