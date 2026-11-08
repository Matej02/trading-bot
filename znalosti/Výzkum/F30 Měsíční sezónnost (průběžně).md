---
tags: [vyzkum, f30, sezonnost, mesicni]
datum: 2026-11-08
---
# F30 Měsíční sezónnost (průběžně, bez lovení)

Z [[Fronta nápadů F22–F33|fronty nápadů]]. Jen test, bot se nemění. Skript `scratch/f30_sezonnost.py`. Viz [[Sezónnost]].

## Plán (zapsán PŘED výpočtem)
**Pravidlo:**
- Pro každý trh a kalendářní měsíc M v roce Y se vezmou výnosy měsíce M za předchozích 10 let (Y−10 až Y−1, potřeba aspoň 8 let).
- **Směr** = znaménko průměru. **Obchoduje se jen**, když aspoň 7 z 10 let mělo stejné znaménko.
- **Vstup** na otevření prvního dne měsíce, **výstup** na zavření posledního dne. Bez SL a TP.
- **Náklady:** půl spreadu brokera relativně k ceně na vstupu i výstupu, swap za každou noc (ze středy na čtvrtek 3×, krypto denně).
- **R** = výnos / směrodatná odchylka měsíčních výnosů daného trhu za předchozích 10 let.

**Trhy:** 39 trhů s denními daty Yahoo z F6, ve skupinách indexy, forex, komodity a krypto.

**Data:**
- **Vývoj:** obchody do 2018.
- **Kontrola:** 2019–2026.
- **Druhý zdroj:** měsíční výnosy z H1 brokera 2019–2026, signál stejný (z Yahoo historie).

**Srovnání:** stále long ve stejných trhoměsících (zachytí obecný růst trhu).

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. Vývoj > 0 a t ≥ 2,0.
2. Kontrola > 0 a t ≥ 1,5.
3. V kontrole aspoň 3 ze 4 skupin > 0.
4. Lepší než stále long ve stejných trhoměsících, ve vývoji i v kontrole.
5. Druhý zdroj > 0.

## Výsledky (2026-11-08)
Souhrn: `research_data/f30/f30_souhrn.txt`.

| Část | n | R | t | stále long stejné měsíce | long signály | short signály |
|---|---|---|---|---|---|---|
| Vývoj do 2018 | 1 594 | **+0,058** | 2,50 | +0,027 | +0,078 | +0,009 |
| Kontrola 2019+ | 1 123 | **−0,102** | **−3,29** | +0,085 | +0,012 | **−0,361** |
| Druhý zdroj (broker) | 973 | −0,107 | −3,17 | +0,090 | +0,010 | −0,391 |

- **Kontrola po skupinách:** forex −0,138, indexy +0,085, komodity −0,329, krypto +0,191 (n 13).
- Ve vývoji to vypadalo dobře (t 2,5), ale od 2019 se sezónnost obrátila. Nejhorší jsou signály proti trhu (short), které dřív sezónnost ukazovala.
- Indexy jsou kladné, protože sezónnost u nich skoro vždy říká long. To je zase jen obecný růst.

**Rozhodnutí:** 1 ANO, 2 NE, 3 NE, 4 NE, 5 NE → **BEZ VÝHODY.** Sezónnost z 10 let zpět do budoucna nefunguje. Do botu ani jako filtr.
