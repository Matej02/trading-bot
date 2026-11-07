---
tags: [vyzkum, f21, indexy, overeni]
datum: 2026-11-07
---
# F21 Noční drift indexů (long přes noc)

Zadání uživatele (2026-11-07): „klidně zkus nový nápad, ale zase zapsat do vaultu mimo a dát zpětně vědět, jak to dopadlo. Na bota nesahat.“
- Bot (runner, simulátor ani jejich kód) se neupravuje.
- Skripty jsou v `scratch/f21_*.py`, výstupy v `research_data/f21/`.

## Proč tento nápad
- **Nový:** ve vaultu zatím netestovaný.
- Poučení z [[F13 indexy na delší historii (HistData 2010–2025)|F13 na delší historii]]:
  - žádná pravidla na úrovni M1 (sweep o tick), jen dvě ceny denně, takže to není citlivé na zdroj dat;
  - jeden obchod denně, takže je hodně obchodů a statistika rychle něco řekne;
  - lze ověřit na nových letech 2010–2019 i na druhém zdroji cen.
- **Známý jev z literatury:** u amerických akciových indexů vzniká většina výnosu přes noc, mezi zavřením a otevřením burzy. Přes den skoro nic. (Cliff, Cooper a Gulen 2008; Lou, Polk a Skouras 2019.)
- Naše pravidla jsou mechanická, nic se neladí.

## Plán (zapsán PŘED výpočtem)
**Pravidlo:** každý obchodní den
- long na zavření svíčky M1 15:59 New York (cena 16:00);
- ven na otevření svíčky M1 9:30 New York následujícího obchodního dne;
- bez SL a TP.

**Náklady jako v testech:**
- nákup za ask (bid + spread brokera podle hodiny + 1 tick), prodej za bid − 1 tick;
- swap long za každou noc, ze středy na čtvrtek 3×.

**Vynechání:** chybí svíčka do ±3 min od 16:00 nebo 9:30, nebo výstup je víc než 4 dny po vstupu.

**Jednotka R:** pohyb po nákladech / ATR20 denního rozpětí (z předchozích 20 seancí). Výsledky i v % ceny.

**Čas:** HistData ve skutečném UTC. Data brokera se v britském letním čase posunou o +1 h na skutečné UTC, viz [[MT5 napojení]].

**Období a trhy:**

| Část | Data | Trhy | Období |
|---|---|---|---|
| Vývoj | HistData | SPX500, NAS100 | 2010-11 až 2019-02-20 |
| Kontrola | broker | SPX500, NAS100 | 2019-02-21 až 2026-10 |
| Druhý zdroj | HistData | SPX500, NAS100 | 2019-02-21 až 2025-12 |
| Jiné trhy | broker | US30 (časy NY); DAX (Frankfurt: zavření 17:30, otevření 9:00) | 2019–2026 |

**Srovnání:**
- denní seance: otevření → zavření stejného dne;
- náhodné okno stejné délky: začátek v náhodnou minutu všedního dne, stejné náklady.

**Pravidla rozhodnutí (pevná):**
- **ANO, výhoda,** pokud platí vše:
  1. Vývoj: průměr po nákladech > 0 a **t ≥ 2,0**.
  2. Kontrola: průměr po nákladech > 0 a **t ≥ 1,5**.
  3. US30 i DAX: průměr po nákladech > 0.
  4. Noční drift je lepší než náhodné okno stejné délky ve vývoji i v kontrole.
- **NE:** cokoliv jiného.
- Časy, filtry ani stop se neladí. Rozpad po dnech v týdnu a po letech je jen popisný.

**Praktická poznámka:** vstup ve 22:00 Praha vyžaduje zapnutý PC nebo server. Pro test to nevadí.

## Výsledky (2026-11-07)
- Souhrn: `research_data/f21/f21_souhrn.txt`.
- Skripty: `scratch/f21_drift.py` a `scratch/f21_graf.py`.

**SPX500 + NAS100:**

| Část | Nocí | R/noc po nákladech | t | % za noc | Bez nákladů | Denní seance | Náhodné okno stejné délky |
|---|---|---|---|---|---|---|---|
| Vývoj (HistData 2010–2019) | 4 067 | **+0,016** | **2,39** | +0,024 % (~6 %/rok) | +0,026 R (t 3,95) | +0,006 R | **+0,036 R** (t 4,97) |
| Kontrola (broker 2019–2026) | 3 312 | **+0,012** | **1,4997** | +0,018 % (~4,6 %/rok) | +0,019 R (t 2,47) | +0,012 R | **+0,023 R** (t 2,72) |
| Druhý zdroj (HistData 2019–2025) | 3 042 | +0,017 | 2,14 | +0,027 % | +0,025 R | +0,007 R | – |

- **Shoda zdrojů:** na 2 734 společných nocích je korelace R **0,98**. Na rozdíl od F13 to na zdroji dat skoro nezávisí.
- **Jiné trhy** (broker 2019–2026):
  - US30: **−0,006 R/noc** (t −0,51);
  - DAX (17:30 → 9:00): +0,002 R (t 0,15).
- **Popisně:**
  - Po dnech vstupu: po +0,028 R, út +0,039 R, st −0,002 R (trojitý swap), čt +0,006 R, pá −0,002 R.
  - Ztrátové roky: 2011, 2016, 2022 (−43 % součtem) a 2023.
  - Nejhorší noc −5,6 % (SPX, 21. 8. 2015). Brexit 23. 6. 2016: −3,5 až −3,7 %.

![[F21 noční drift – kumulativně.png]]

## Rozhodnutí podle pravidel zapsaných předem
1. Vývoj > 0 a t ≥ 2,0: **ANO** (t 2,39).
2. Kontrola > 0 a t ≥ 1,5: **NE** (t 1,4997, těsně pod hranicí; hranice se neposouvá).
3. US30 i DAX > 0: **NE** (US30 −0,006 R).
4. Lepší než náhodné okno stejné délky: **NE**. Náhodná okna vyšla v obou obdobích asi dvakrát lépe.
   - Ani bez tohoto bodu by se rozhodnutí nezměnilo (2. a 3. také neprošly).

**⇒ BEZ VÝHODY.**
- Být long na US indexech 2010–2026 vydělávalo, ale to je obecný růst trhu (beta), ne načasování.
- Noční okno nepřineslo víc než libovolné okno stejné délky.
- Efekt z literatury (výnos hlavně přes noc) se v CFD datech po nákladech neprojevil silněji než náhoda. Na US30 a DAXu není vůbec.
- Kladné úterý a pondělí je jen popisné, k obchodování se nepoužívá. Šlo by o vybírání z 5 řezů a další nezávislá US data nemáme.
