---
tags: [koncept, volume]
aktualizovano: 2026-10-29
---
# Volume profile (POC, VAH, VAL, HVN, LVN)

Bin = denní ATR / 40, objem svíčky rovnoměrně přes rozsah; POC = nejvíc objemu, Value Area 70 %,
HVN/LVN z vyhlazeného histogramu. Profily denní, kompozitní 20 dní, fixed range.
Strategie: VAL/VAH → POC ([[F5 SMC a volume profile na 1h|F5]], −0,25 R), rotace ve VA a pravidlo 80 % a breakout přes LVN
([[F7 Dokument 6 strategií SMC|F7]], ztrátové). Na forexu jen tick volume. Souvisí s [[Režim trhu]], [[Supply a demand zóny]].

## Definice z dokumentu
- Bin = denní ATR(14) / 40 (zaokrouhlený na tick); objem M1 svíčky rovnoměrně mezi biny od low po high.
- POC = bin s největším objemem; Value Area 70 %: od POC přidávat větší ze dvou sousedních dvojic binů.
- HVN/LVN: vyhlazení 5 biny; HVN = lokální max ≥ 50 % POC; LVN = lokální min ≤ 25 % POC mezi dvěma HVN.
- Profily: denní (pdPOC/pdVAH/pdVAL), kompozitní 20 dní, fixed-range. Naked POC (posledních 10 dní) jako magnet pro TP.

Zdroj: [[Dokument 6 strategií SMC + Volume Profile|dokumentu 6 strategií]].

## Z materiálů FM (část 1)
- **HVN** = magnet a S/R. **LVN** = cena projede; **vstup na zóně uvnitř LVN je riskantní** a chce další potvrzení.
- **Value Area 70 %:** uvnitř rotace kolem POC. Acceptance mimo VA se silným objemem znamená trend; rejection se slabým objemem návrat.
- **nPOC** (neotestovaný POC předchozí seance) = magnet a target (Šrajer, Můčka, Hakimi). V TradingView zapnout „Extend POC right“.
- **Tvary:** D = balance, P = short covering, b = long liquidation, thin = rychlé průrazy.
- **Session profily:** Asie má profil D (mean reversion), Londýn průraz nebo fakeout Asie, NY testuje POC/VAH/VAL Londýna.
- **Fixed range** přes trend nebo korekci (Valchář): POC/HVN, který se kryje se S/D zónou, je potvrzení.
- U forexu je profil jen z tick volume → [[Futures data a objem]].
