---
tags: [projekt, prop, runner, navrh]
datum: 2026-11-25
---
# Návrh pravidel prop runneru (FTMO 2 kroky Swing)

Zadání uživatele (2026-11-25): „Klidně to udělej.“ **Jen návrh. Bot ani runner se nemění.** Zavedení až na pokyn uživatele, až budou splněné podmínky startu (níže). Vychází z [[Cesta k prop účtu]], [[F87 Měřítko s F33 se stopem jako v runneru|F87]], [[F89 Porovnání zkoušek FTMO 1 krok a 2 kroky|F89]], [[F90 Denní pojistka na celý účet|F90]], [[F91 Pravidla prop firem v měřítku|F91]].

## Kdy se začne (podmínky startu)
1. **RSI(2) projde sledováním dopředu:** ≥ 30 uzavřených obchodů v simulátoru, R ≥ 0, výhry ≥ 60 %, série ztrát ne horší než v testu, bez technických odchylek ([[F42 RSI(2) přísná prověrka]]). Odhad 8–10 měsíců od 19. 11. 2026.
2. **Technické vyhodnocení dema 4. 1. 2027** bez neopravených chyb ([[FM live test na MT5 demu]]).
3. **VPS** (runner musí běžet celý den i v noci, F33 končí 21:55, pojistka hlídá stále).
4. **Zkušební běh na FTMO Free Trial** 2–4 týdny se všemi pravidly níže.
5. Nákup zkoušky a přihlášení dělá uživatel. Heslo nikdy nezpracovává Claude.

## 1. Co obchoduje
- Jen ověřené strategie: **F33 se stopem 3 ATR** a **RSI(2)** (až po bodu 1 výše). F31 jen pokud projde ověřením.
- F12–F16, F20 a další neověřené systémy na prop účtu **vypnuté**.
- Riziko **1,25 % počátečního kapitálu na obchod** (bezpečné riziko podle F87/F89: do 36 měsíců projde 65 %, propadne 3 %).

## 2. Ochrana účtu
- Runner obchoduje **jen na čísle účtu, které zadá uživatel** v konfiguraci. Na jiném účtu odmítne obchodovat.
- Před každým vstupem kontrola: správný server, symbol a velikost lotu v mezích FTMO.

## 3. Denní pojistka (z F90, odolná varianta)
- Limit FTMO dne: L = max(zůstatek o půlnoci času serveru − 5 000 $, 90 000 $) na účtu 100k.
- **Pojistka zavře všechny pozice, když equity klesne na L + 2 000 $.** Tedy denně −3 %, celkem 92 000 $.
- Po zásahu se **do půlnoci (čas serveru) neotevírá nic nového**, pak běží normálně.
- Kontrola equity aspoň **každých 10 s** (dnes runner tiká po minutě, na prop zrychlit).
- Upozornit: F90 tuhle variantu vybral až po výsledku. Je to ochrana, ne zrychlení. Před startem ověřit na Free Trialu, jak rychle se pozice zavírají.

## 4. Neaktivita (podmínky FTMO čl. 13.2.3)
- FTMO může účet ukončit po **30 dnech bez otevření obchodu**. Naše strategie mají mezeru > 30 dní asi 2–3× ročně (nejdelší 154 dní).
- **Udržovací obchod:** když od posledního otevřeného obchodu uplyne **27 dní**, runner otevře nejmenší lot na US500 a do minuty ho zavře. Ve stejný den upozorní uživatele.
- Odhad: ~4–5× ročně, náklad jen spread nejmenšího lotu.
- **Riziko:** FTMO má právo uvážení (věta o „obcházení“ je v podmínkách u ztráty 8–10 %). Jistotu bez dotazu na podporu nemáme. Alternativa: víc strategií (F93, pokud projde).

## 5. Fáze zkoušky
- Cíl fáze (+10 %, pak +5 %): když equity na zavření dne dosáhne cíle a jsou splněné **4 obchodní dny**, runner **zavře všechny pozice a přestane obchodovat**. Upozorní uživatele.
- FTMO hodnotí jen se zavřenými pozicemi.
- Druhá fáze a financovaný účet: nové přihlašovací údaje zadává uživatel, runner se jen přepne na nové číslo účtu (bod 2).

## 6. Čas a symboly
- Čas serveru FTMO (SEČ/SELČ). Půlnoc serveru = reset denního limitu.
- Symboly FTMO (např. US500.cash, US100.cash), velikost kontraktu, nejmenší lot a swap **ověřit na Free Trialu**. Dnes runner obchoduje SPX500mini a NAS100mini u jiného brokera.
- F33: vstup 15:30, výstup 30. den v 21:55 (čas Praha) beze změny.

## 7. Záznamy a upozornění
- Deník: každý vstup, výstup, zásah pojistky, udržovací obchod, denní equity o půlnoci.
- Upozornění uživateli: zásah pojistky, udržovací obchod, splněný cíl fáze, výpadek spojení > 5 min.

## 8. Co se před zavedením otestuje
- Jednotkové testy: výpočet L, pojistka, 27denní počítadlo, zastavení po cíli, odmítnutí cizího účtu.
- Free Trial 2–4 týdny: skutečné zavírání pojistkou, symboly, velikosti lotů, čas serveru.
- Až potom nákup zkoušky (rozhoduje uživatel).

## Stav (2026-11-25)
- Na pokyn uživatele („připrav vše, ať je ready na přenesení“) **naprogramováno** v `prop/run_prop.py`: 17 testů prošlo, shoda s testy na historii 100 % (813/813). Demo runner beze změny. Postup: [[Prop runner – návod k přenesení]].
