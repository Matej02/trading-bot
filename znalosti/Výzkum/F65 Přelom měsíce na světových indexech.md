---
tags: [vyzkum, plan]
datum: 2026-11-20
---
# F65 Přelom měsíce na světových indexech

Zadání uživatele (2026-11-20): „Ok, oprav to páteční a stáhni ty indexy.“ Cíl: nezávislé ověření kandidáta [[F61 a F62 Ověření kandidátů (přelom měsíce v Evropě, zlato v Asii)|F61]] (přelom měsíce v Evropě) na trzích, které se při F55 ani F61 nepoužily. Plán je zapsaný **před stažením a výpočtem**. Pravidla se po výsledku nemění.

## Data
Yahoo denní, co nejdelší historie, stažené se souhlasem uživatele do `research_data/f65` (surový JSON). Deset trhů:

| Region | Index (Yahoo) |
|---|---|
| Japonsko | Nikkei 225 (^N225) |
| Austrálie | ASX 200 (^AXJO) |
| Švýcarsko | SMI (^SSMI) |
| Nizozemsko | AEX (^AEX) |
| Belgie | BEL 20 (^BFX) |
| Hongkong | Hang Seng (^HSI) |
| Kanada | TSX (^GSPTSE) |
| Jižní Korea | KOSPI (^KS11) |
| Tchaj-wan | TAIEX (^TWII) |
| Singapur | STI (^STI) |

**Čištění dat:**
- řádky bez rozpětí (otevření = max = min = zavření) se vyhodí;
- roky, kde otevření chybí nebo se rovná předchozímu zavření ve více než 50 % dní, se vyřadí, protože vstup je na otevření;
- víkendy pryč.

## Pravidlo (stejné jako F55 a F61)
- **Obchod:** long od otevření posledního obchodního dne měsíce (podle dat trhu) do zavření 3. obchodního dne dalšího měsíce.
- **Srovnání:** všechna ostatní stejně dlouhá okna (otevření dne i → zavření dne i+3).
- **R** = výsledek / ATR20.
- **Náklady:** tyhle trhy broker nemá, proto paušál podle evropských indexů: 2 bp na vstupu i výstupu a swap −1 bp za noc (středa 3×).
- Převis = signál − srovnání, Welch t, po dnech (průměr přes trhy).

## ANO jen když platí vše
1. Všech 10 trhů dohromady, celé období: signál > 0, převis > 0, t ≥ 2,0.
2. Všech 10 trhů dohromady, 2019–2026: signál > 0 a převis > 0.
3. Převis > 0 aspoň na 7 z 10 trhů (celé období).
4. Převis kladný aspoň v 55 % let.

**Co z výsledku plyne:**
- **Projde:** F61 má první nezávislé potvrzení. Pořád jen simulátor; MT5 až po sledování dopředu a se souhlasem.
- **Neprojde:** F61 zůstává jen „skoro“ kandidát. Jeho sledování v simulátoru se nemění.

Skript `scratch/f65.py`, stažení `scratch/f65_stahni.py`, výstup `research_data/f65/souhrn.txt`.
