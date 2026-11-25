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

Doporučení konkrétních firem: [[Prop firmy – doporučení]] (2026-11-11).

- **2026-11-19 ([[F52 Kombinace F33 a RSI(2) pro prop účet|F52]]):** F33 + RSI(2) dohromady asi +4 R ročně, korelace 0,07, největší propad −7,9 R (2003–2026). Při 1 % riziku asi +4 % ročně a propad do −8 %. Zkouška +10 % za 12 měsíců jen při 2 % (54 %), proto firma bez časového limitu a 1–1,5 % riziko.

- **2026-11-25 – upřesnění uživatele:** ostrý obchod bude jen přes prop zkoušku, ne vlastních 10 000 Kč. Malý účet a broker s mikroloty ([[F70 RSI(2) pro malý účet|F70]]) se tedy neřeší. VPS až před ostrým startem. Výzkum se má měřit podle toho, o kolik zkrátí zkoušku.

- **2026-11-25 ([[F90 Denní pojistka na celý účet|F90]], [[F91 Pravidla prop firem v měřítku|F91]]):** firma = FTMO 2 kroky Swing. Pro runner na prop účtu (až na pokyn) přibývají dva požadavky: 1) denní pojistka (odolná varianta −3 % za den / 92 % celkem, potřebuje běh celý den = VPS), 2) neaktivita: FTMO může ukončit účet po 30 dnech bez nového obchodu (podmínky čl. 13.2.3). Řešení: víc strategií, nebo udržovací obchod před uplynutím 28 dnů (~4–5× ročně).
