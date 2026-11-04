# Fronta: všechny FM strategie podle PDF + doplňujících pravidel, pak live (zadání uživatele 2026-11-03)

Zadání (doslova): „doufám že tento word jsi pouze dal jako doplňující informace a ne jako čistý zdroj informací…
vše ať je v obsidiánu a pak testuj vše jak jsme se domluvili když budeš spouštět testování a vše dej live“.

**Postup u každého mentora:**
1. Celý text PDF + všechny obrázky jeho galerie + navazující Základy.
2. Doplňující pravidla (Word) jen jako dodatek: zpřesňují, co v PDF není.
3. Plán s odkazy na lekci a stranu.
4. Test (vývoj/OOS, náhoda, bez nákladů, vrstvy).
5. Vault.
6. Live v simulátoru jako experiment.

| # | Strategie | Test | Live |
|---|---|---|---|
| 1 | Můčka (B1) | F12 hotovo 2026-11-03: OOS +0,06 R, bez výhody | `fm12_mucka_m1` pushnuto (shoda 19/21) |
| 2 | Veselovský (B2: OB, likvidita, FVG, SVP) | F13 hotovo: indexy OOS +0,23 R, nejlepší FM, neověřeno | `fm13_ves_m1` pushnuto (shoda 49/49) |
| 3 | Pátek (B3: S/R, trendovky, fakeout) | F14 hotovo 2026-11-04: OOS +0,12 R, náhoda +0,21 R → bez výhody | `fm14_pat_m15` pushnuto (shoda 33/34) |
| 4 | Hvězda (B4: S/D W1/D1, base 1–3, COT) | rozpracováno: text + 128 obrázků prošlé, plán `F15_PLAN.md`, kód zatím ne; COT data chybí (stažení z cftc.gov čeká na souhlas) | |
| 5 | Hakimi (B5: Elliott, zóny) | | |
| 6 | Šrajer DT + swing (B6) | | |
| 7 | Valchář (OB limitkou, POC) | | |
| 8 | Kimmel (indexy ICT) | | |
| 9 | Obecná strategie uživatele (část A: ranní top-down, SFP s FRVP) | | |

**Omezení simulátoru:** Yahoo 1m jen 5 dní, 5m/15m 1 měsíc, 1h 1 rok. Vstup je trhem na zavření svíčky; limit se nahrazuje
signálem na svíčce, která úroveň zasáhne. FM systémy blokuje Risk expozicí měn, kterou zaplní Momentum (export 2026-11-03).

**2026-11-03: Vercel nenasazuje od 2026-10-29** (pole `build` v `/api/tick/status` chybí) – opravuje uživatel ve Vercelu.
