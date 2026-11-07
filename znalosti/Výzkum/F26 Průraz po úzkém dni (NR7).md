---
tags: [vyzkum, f26, denni, prurazy]
datum: 2026-11-07
---
# F26 Průraz po úzkém dni (NR7)

Z [[Fronta nápadů F22–F33|fronty nápadů]]. Jen test, bot se nemění. Skript `scratch/f26_nr7.py`.

## Plán (zapsán PŘED výpočtem)
**Pravidlo (denní svíčky):**
- **NR7:** rozpětí dne (H − L) je nejmenší ze 7 dní včetně dneška. Signál na zavření.
- **Další den:** stop nad H a pod L dne NR7.
  - Otevření nad H → long za otevírací cenu. Pod L → short.
  - Jinak vstup na úrovni H nebo L.
  - Když jsou ten den proraženy obě strany, nevíme, která první. Počítá se jako stop (−1 R), protože SL první strany je druhá strana.
- **SL:** druhá strana dne NR7. Kontrola denně (Low/High), při gapu přes SL za otevírací cenu.
- **Výstup:** na zavření 3. dne po dni vstupu, bez TP.
- **Náklady:** spread brokera relativně k ceně (medián spreadu / dnešní cena × cena) na vstupu i výstupu, swap za každou noc (ze středy na čtvrtek 3×, krypto denně).

**Trhy:** všech 39 trhů s denními daty z F6 (Yahoo), ve skupinách indexy, forex, komodity a krypto.

**Data:**
- **Vývoj:** Yahoo do 2018-12-31.
- **Kontrola:** Yahoo 2019–2026.
- **Druhý zdroj:** denní svíčky brokera z H1 2019–2026 (trhy, které H1 mají).

**Náhoda:** stejný trh, náhodný den stejného období, stejný směr, SL ve stejném násobku ATR20, stejný výstup.

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. Vývoj > 0 a t ≥ 2,0.
2. Kontrola > 0 a t ≥ 1,5.
3. V kontrole aspoň 3 ze 4 skupin trhů > 0.
4. Lepší než náhoda ve vývoji i v kontrole.
5. Druhý zdroj > 0.

## Výsledky (2026-11-07)
- Souhrn: `research_data/f26/f26_souhrn.txt`.
- **Čištění dat (oprava chyby, bez vlivu na pravidla):** vyřazeny denní svíčky Yahoo s nulovým rozpětím nebo s cenami mimo High–Low.

| Část | n | R | t | náhoda |
|---|---|---|---|---|
| Vývoj Yahoo do 2018 | 18 832 | **+0,032** | 2,12 | −0,005 |
| Kontrola Yahoo 2019+ | 8 485 | **−0,039** | −1,30 | −0,054 |
| Druhý zdroj (broker H1 → D1) | 7 361 | **−0,071** | −3,30 | – |

- **Kontrola po skupinách:** forex −0,165, indexy +0,008, komodity +0,391, krypto +0,284.
- **Indexy:** 1980–1999 **+0,35 R**, 2000–2018 +0,11 R, 2019+ +0,01 R. Výhoda z doby, kdy to Crabel publikoval, postupně zmizela.
- **17–24 % signálů prorazí obě strany ve stejný den** a skončí na stopu (−1,05 R). To sežere zisk ostatních obchodů.
  - Obchody bez takových dní jsou +0,2 až +0,3 R, ale vyřadit je jde jen zpětně (pohled do budoucnosti), proto se nepočítají.

**Rozhodnutí:** 1 ANO, 2 NE, 3 ANO, 4 ANO, 5 NE → **BEZ VÝHODY.**
