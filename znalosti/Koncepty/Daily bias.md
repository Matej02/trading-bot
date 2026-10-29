---
tags: [koncept, cas]
aktualizovano: 2026-10-29
---
# Daily bias
Zdroj: FM (Veselovský, Můčka, Kimmel, Hakimi) · Skupina: čas / kontext

## Definice
Předpokládaný směr dne z denní svíčky a likvidity. Obchoduje se **jen ve směru biasu**, bias se během dne nemění.

## Jak ho poznat (mechanicky)
**Veselovský** (udává 70–80 % úspěšnost):
- Close těla **nad PDH** → dnes nahoru (pokračování).
- **Sweep PDH a close pod ním** → dnes dolů na PDL. Zrcadlově pro PDL.
- Close uvnitř knotu: nad 50 % knotu bullish, pod 50 % bearish.
- Range: neobchodovat, dokud se neuzavře mimo něj.
- K tomu D1 FVG a OB a vztah close k včerejšímu targetu.

**Můčka:** po **bearish denní svíčce cílit na PDL, po bullish na PDH** („velká pravděpodobnost“). Totéž s W a M svíčkami.
Další faktory: HTF, PA, session (Asie, Frankfurt) a **VWAP z předchozího dne**.

**Kimmel:** kde jsme a kam se dnes pravděpodobně pohneme (nejbližší interní nebo externí likvidita).

## Obchod
Filtr směru pro intraday modely ([[Daily Open a Power of 3]], [[MSS a displacement]]). Target dne = PDH/PDL.

## Souvisí s
[[Likvidita]] · [[Horizontální levely]] · [[Daily Open a Power of 3]] · [[SFP – sweep likvidity]]

## Otestováno
**Zatím ne. Rychlý a levný test na D1:** pro každý den spočítat pravidlo a pak zjistit, zda dosáhne cíle (PDH/PDL)
dřív než opačné strany. Srovnat s nepodmíněnou mírou (kolikrát se PDH/PDL trefí bez pravidla). Tisíce dní, víc trhů.

## Otestováno – F8 (2026-10-29)
Zásah cíle 62–65 % (opačný směr 29–31 %), ale cíl je blízko (0,35 R).
Obchod open → PDH/PDL, SL opačný extrém: **−0,06 R** (DEV i OOS), opačný směr −0,16 až −0,19 R.
Slabý směrový náklon, samostatně neobchodovatelné. → [[F8 Strategie z FM PDF]]

F9 (2026-10-29): jako spouštěč i filtr v 2 208 kombinacích ([[F9 Kombinace FM konceptů]]) – bez výhody.
