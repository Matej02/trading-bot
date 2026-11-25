---
tags: [projekt, prop, runner, navod]
datum: 2026-11-25
---
# Prop runner – návod k přenesení

Zadání uživatele (2026-11-25): „Prostě připrav vše, aby bylo ready na přenesení, já to pak koupím, i VPS pak koupím.“
Pravidla: [[Návrh pravidel prop runneru]]. Demo runner `run_fm_demo.py` se nemění, prop runner je samostatný.

## Co je hotové
| Soubor | Co dělá |
|---|---|
| `prop/run_prop.py` | Runner: F33 se stopem 3 ATR + RSI(2), riziko 1,25 % počátečního kapitálu, denní pojistka (−3 % / 92 %), kontrola rizika před vstupem, udržovací obchod po 27 dnech, stop po splnění cíle fáze, zámek na číslo účtu |
| `prop/prop_config.example.json` | Vzor nastavení (zkopírovat jako `prop_config.json`) |
| `prop/test_run_prop.py` | 17 testů s falešným MT5, **všechny prošly** (25. 11. 2026) |
| `prop/parita.py` | Shoda s testy na historii: **F33 200/200, RSI(2) 613/613 (100 %)**, výstup `research_data/prop/parita_prop_runneru.txt` |
| `f2x_live.py` (kořen) | Pravidla F33 a RSI(2), stejná jako demo a simulátor (runner je importuje) |

**Rozdíly proti demu (záměrné, blíž testům):**
- RSI(2): signál, SMA200, SMA5 i ATR z Yahoo jako v testu F42. Vstup 9:30–9:45 NY (test: otevření dalšího dne), výstup 15:50–15:58 NY podle aktuální ceny (test: zavření dne).
- F33: ATR z Yahoo indexu jako v testu.
- Denní limit FTMO se nuluje o **půlnoci Praha**. Zůstatek o půlnoci runner dopočítá z historie obchodů, takže funguje i po restartu.
- Kontrola pojistky každých 10 s, strategie každou minutu.

## Kroky (uživatel → Claude)
1. **Free Trial FTMO** (uživatel, zdarma): registrace, MT5 účet. Heslo jen v MT5, nikdy do chatu ani souborů.
2. **Ověřit na Free Trialu** (spolu):
   - názvy symbolů (US500.cash, US100.cash, US30.cash?), velikost kontraktu, nejmenší lot;
   - čas serveru (+2/+3 h);
   - že je zapnuté „Algoritmické obchodování“.
   - Při jiných názvech se upraví jen `symbols` v configu.
3. **Zkušební běh na Free Trialu 2+ týdny:**
   - `prop_config.json`: login = číslo Free Trial účtu, `target_pct` 10;
   - nejdřív `py run_prop.py --once` (suchý běh, nic neposílá), pak `py run_prop.py --live`.
   - Na tomhle PC běží demo runner, proto pro FTMO **druhá instalace MT5** (vlastní složka, `terminal_path` v configu). Spouští ji uživatel.
4. **VPS** (uživatel): Windows, Python 3.13, `pip install MetaTrader5`. Zkopírovat složku `prop` + `f2x_live.py` do stejné struktury (`…\Trading bot\prop\` a `…\Trading bot\f2x_live.py`). Nainstalovat MT5 od FTMO, přihlásit se ručně.
5. **Lednová brána** (Claude, 4. 1. 2027): demo a simulátor bez nevysvětlených chyb, Free Trial bez technické chyby, pojistka ověřená, VPS běží, RSI(2) dopředu ne horší než nejhorší období testu.
6. **Koupě zkoušky** (uživatel): FTMO 2 kroky, Swing, 100k. Do configu nový login, `phase_start` = den koupě, `target_pct` 10. Spustit `--live`.
7. **Fáze 2:** nový login, `target_pct` 5, nový `phase_start`. **Financovaný účet:** `target_pct` null.

## Na co dát pozor
- Runner obchoduje jen na účtu z configu. Na jiném účtu skončí.
- Po zásahu pojistky nebo splnění cíle vyskočí okno a zapíše se `prop/prop_log.txt` a `prop_journal.jsonl`.
- Termíny FOMC a svátky NYSE v `f2x_live.py` jsou do konce 2027. Doplnit včas.
- `prop_config.json`, stav a deník jsou v `.gitignore`, do veřejného repozitáře nejdou.
