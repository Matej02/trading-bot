---
tags: [fm, zdroj, strategie, daytrading, ict, indexy]
zdroj: "D:\\youtube\\FM pdfka\\Strategie\\Rafael Kimmel - Day Trading Strategie (PDF)"
zpracovano: 2026-10-29
---
# FM – Rafael Kimmel: Day Trading indexových futures (NQ/ES, daily bias + PDH/PDL + MSS)

15 PDF, 80 stran. Obchoduje **NQ a ES** (futures) přes futures prop firmy (Apex, Topstep, MFF).
Přístup je ICT: „funkční koncepty, jednoduchost“. Viz [[FM materiály]].

## Strategie
- **Best pair:** NQ a ES většinou korelují. Při bullish biasu se obchoduje ten z nich, který je víc bullish
  (silnější vůči biasu), při bearish ten slabší. Je to obdoba SMT divergence.
- **Okno:** u indexů je volatilita předvídatelná, **15:30–19:00 CET**. Entry model 1 jen **15:30–18:00**.
  Exekuce na M15–M1; čím konzervativnější, tím vyšší TF.
- **Daily bias:** kde jsme a kam se cena pravděpodobně pohne dnes, tedy nejbližší interní nebo externí likvidita.
  → [[Daily bias]]
- **Změna struktury:** „Body tells the story, wicks do the damage“, rozhodují jen **close svíček**.
  Varianta 2 (první známky změny) je agresivnější a má lepší RR; hodí se v rychlém trhu s jasným biasem.

### Entry model 1: reverzní
1. Trh je v souladu s denním biasem.
2. **Dotyk oblasti z předchozího dne** (PDH/PDL, zóna předchozího dne) na M15.
3. Reverzní signál (změna struktury) na **M5** (konzervativně) nebo **M1** (agresivně).
4. **SL 25 % za nejbližší high/low.** Příklad: vzdálenost 20 $ → SL 25 $.

### Entry model 2: pokračovací
1. Trh je v souladu s denním biasem.
2. Dotyk S/D zóny na M15.
3. **2 po sobě jdoucí změny struktury ve směru biasu.**
4. Vstup v nejbližší S/D zóně. **SL za 3 předchozí body zájmu** (S/D zóny a FVG), konzervativně za 4.

### Targety
- **Interní likvidita je bezpečnější než externí** („headache to reward“).
  Lepší je vybrat 1,9R na interní likviditě než o 0,1R minout 2R na externí.
- **Extreme zóna** = poslední S/D zóna. Tam vybírat zisk, protože přichází pullback.
- **Trifecta:** strike rate, frekvence a RR; nejde mít všechny tři vysoko.

## Risk management (futures prop) → [[Risk management]]
- **Challenge Apex:** riskovat polovinu nebo celý drawdown, splnit v 1–2 obchodech (1:1 až 1:1,2).
- **Topstep:** 25–50 % DD, pozor na consistency rule.
- **Funded:** **10–20 % dostupného drawdownu na obchod** (10 % = ~10 ztrát v řadě, 20 % = ~5).
- **Osobní účet:** max. 1 %.
- **Velikost pozice:** risk $ / SL v bodech / hodnota bodu (NQ mini 20 $/bod, micro 2 $; ES mini 50 $, micro 5 $).
- **Metrika:** payout / (challenge + activation fee).

## Testovatelnost
**Dobrá na US100/US500 z MT5.**
- Model 1: dotyk PDH/PDL v 15:30–18:00, změna struktury na M5, SL 1,25× vzdálenost k extrému, TP interní likvidita.
- Best pair jde měřit relativní silou NQ vs ES od open.
- Souvisí s [[SFP – sweep likvidity]] na PDH/PDL; F7 ho na indexech moc nezkoušelo (hlavně krypto, forex a zlato).

## Z grafů v PDF (prohlédnuto všech obrázků, 2026-10-29)
- **Entry model #1 (diagram):**
  - Range nad **15m PDA** (premium/discount array, zóna z předchozího dne, šedý box).
  - Cena sweepne pod 15m PDA (stop hunt), vrátí se nad **market structure shift** a vznikne **LTF FVG**.
  - Vstup long v LTF FVG, SL pod sweep low (+25 %), TP nad range. Na NQ ukázkách RR ~2–3.
- **Entry model #2:** dvě po sobě jdoucí **MSS (1, 2) na 15m** ve směru biasu po dotyku 15m zóny.
  Vstup na retestu zóny po druhém MSS (hvězdička), SL nad MID/high. RR ~3–4.
- **Market shift = close těla za úrovní.** „NOT a market shift“ = jen knot přes úroveň; „Market shift“ = tělo uzavře nad.
- **Likvidita (diagram):** nad trhem external liquidity (swing high), uvnitř řada internal liquidity (menší high a low).
  Cena postupně vybírá interní a pak externí.
- **Targets:**
  - IRL linky uvnitř range, ERL na okraji, **„Extreme“ = poslední zóna** (šedý box na konci).
  - TP se bere před extreme zónou nebo na poslední interní likviditě.
- **Bias (cvičení):** horizontály předchozího high a low dne, cíl = nejbližší likvidita.
- **NQ vs ES:** stejná seance, jeden víc bullish (best pair).

## Otestováno – F10 (2026-10-29)
Entry model přesně podle PDF na minutových datech, OOS 2022–26: **model 1 −0,04 R (n 186), model 2 −0,11 R**, bez výhody. → [[F10 Entry modely mentorů FM]]
