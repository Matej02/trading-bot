---
tags: [projekt, prop, plan]
datum: 2026-11-11
---
# Cesta k prop účtu (plán, 2026-11-11)

Otázka uživatele: „Jak je možné se dopracovat k tomu, abychom tohle mohli používat přes prop účet?“

**Úzké místo není technika, ale ověřená výhoda.** Teď prošla jen [[F33 Rebalancování na konci měsíce|F33]], [[F31 Drift před FOMC|F31]] je kandidát. Samotná F33 dává 1–3 % ročně. Zkoušku (+10 % a +5 %) by při bezpečném riziku dělala roky, při riziku 5 % propadne v 51–64 % případů ([[Požadavky a nápady uživatele|výpočet 11. 11.]]).

## Kroky
1. **Víc ověřených strategií** (průběžně, výzkum).
   - Stejný postup jako dosud: plán předem, starší roky, druhý zdroj.
   - Cíl: několik nezávislých strategií, dohromady aspoň ~8–10 % ročně při riziku, které nepřekročí limity.
   - Bez toho prop nedává smysl.
2. **Technické ověření na demu** do konce prosince, vyhodnocení 4. 1. 2027 ([[FM live test na MT5 demu]]).
3. **Výběr prop firmy.** Uživatel vybere 2–3 kandidáty, Claude porovná jejich veřejná pravidla:
   - MT5 a povolené EA / automatické obchodování;
   - bez časového limitu zkoušky;
   - držení přes noc a víkend (F33 drží 2–4 dny);
   - žádné rušení účtu za neaktivitu (F33 obchoduje ~8× ročně);
   - pravidla kolem zpráv;
   - pravidlo konzistence (zisk soustředěný do pár dní může vadit);
   - denní limit z equity nebo zůstatku, statický nebo klouzavý max. propad;
   - specifikace indexových CFD (minimální lot a $/bod; při malé velikosti účtu F33 nevejde);
   - cena, podíl na zisku, výplaty.
4. **Úprava runneru pro prop** (až na pokyn uživatele, teď se bot nemění):
   - povolený jen konkrétní účet, který zadá uživatel;
   - vlastní pojistky pod limity firmy (např. stop obchodování při −3 % za den a −8 % celkem);
   - SPX a NAS brát jako jedno riziko (korelace 0,9);
   - pravidla firmy (zprávy, víkend).
5. **Spolehlivý běh:** PC se ve 20:00 vypíná, F33 končí ve 21:55. Pro prop je potřeba PC zapnutý, nebo VPS (placené).
6. **Zkušební „papírová zkouška“** na demu s pravidly vybrané firmy 1–2 měsíce plus simulace na historii (pravděpodobnost projití, propadnutí, očekávaná hodnota vůči poplatku).
7. **Rozhodnutí a start dělá uživatel:**
   - koupí zkoušku;
   - přihlásí MT5 k prop účtu (heslo zadává sám);
   - přepne runner.
   - Claude na prop účtu sám neobchoduje a hesla nezpracovává.

## Realistický odhad
- Kroky 3–6 technicky zaberou několik týdnů.
- Termín určuje krok 1. Dokud není portfolio ověřených strategií, prop zkouška má podle výpočtu spíš zápornou očekávanou hodnotu (poplatek).
