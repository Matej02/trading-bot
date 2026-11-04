---
tags: [koncept, fundament]
aktualizovano: 2026-10-29
---
# Makro skóre měn (Trading Analyzer)
Zdroj: FM ([[FM Strategie – Jan Šrajer (day + swing)|Šrajer]], Valchář, Veselovský) · Skupina: fundament

## Definice
Každá z 8 měn dostane skóre ze sentimentu, ekonomiky a techniky. **Skóre páru = součet složek (−18…+18)**,
podle něj je bias. Nástroj je placený, metodika je v [[FM Strategie – Jan Šrajer (day + swing)|Šrajerových PDF]].

## Jak ho poznat (mechanicky)
| Složka | Rozsah | Složka | Rozsah |
|---|---|---|---|
| COT | −3…+3 | Úrokové sazby | −2…+2 |
| Retail sentiment (kontrariánsky) | −1…+1 | Manufacturing PMI | −2…+2 |
| GDP | −2…+2 | Services PMI | −2…+2 |
| CPI | −3…+3 | Retail sales | −2…+2 |
| Zaměstnanost | −4…+4 | Sezónnost | −2…+2 |
| | | Trend | −2…+2 |

- **Bias:** ≤ −9 velmi medvědí, −8…−5 medvědí, −4…+4 neutrální, +5…+8 býčí, ≥ +9 velmi býčí.
- **Signál = změna skóre o ≥ 2 body**, ne absolutní hodnota.
  Příklad: EURJPY −3 → 0 je býčí, i když cena padá; čeká se pullback a vstup ze zóny.
- Valchář: sleduje **momentum skóre**. Range a otáčející se skóre předznamenávají obrat;
  divergence cena–skóre dává protitrendový vstup ze silné S/D.

## Data
**Historie skóre je k dispozici:** 28 párů, denně 2017-01-01 (CAD páry od 2020-11-30) až 2024-10-03.
Leží v `research_data/fm_score/*.csv` (sloupce `timestamp, score`). Zdroj: FM, Šrajer swing, „3. Praxe data“.
Pozor: není jasné, zda je hodnota z rána nebo z večera. Při testu vstupovat až další den.

## Obchod
Pár se změnou skóre ≥ 2 → zóna ve směru změny → pullback → vstup, SL za zónu.

## Souvisí s
[[COT]] · [[Sezónnost]] · [[Carry]] · [[DXY a dolar]] · [[Zprávy a kalendář]]

## Otestováno
**Zatím ne. Silný kandidát:** reálná data skóre + D1 ceny z MT5 umožní ověřit „změna ≥ 2 → směr“ a „bias ±5 → trend“ proti náhodě.

## Otestováno – F8 (2026-10-29)
Změna skóre o ≥ 2 body → výnos za 5–20 dní −0,07 až +0,03 ATR, zásah ~49 % (DEV 2017–21 i OOS 2022–24). Bias |skóre| ≥ 5 → ~0.
**Bez výhody.** → [[F8 Strategie z FM PDF]]

## Otestováno – F17/F18 (2026-11-04)
Skóre jako filtr Šrajerova swingu (bias ±5 / změna ±2) a Valchářových OB (momentum): v OOS vždy horší než bez filtru (−0,37 až −0,42 R). [[F17 Šrajer day a swing podle PDF]], [[F18 Valchář podle PDF a obrázků]]
