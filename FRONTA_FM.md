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
| 4 | Hvězda (B4: S/D W1/D1, base 1–3, COT) | F15 hotovo 2026-11-04 (COT z CFTC): OOS −0,17 R, COT nepomohl → bez výhody | `fm15_hve_h1` pushnuto (shoda 7/11 při stejné délce historie) |
| 5 | Hakimi (B5: Elliott, zóny) | F16 hotovo 2026-11-04: OOS +0,07 R jen zlato, jinde ztráta → bez výhody | `fm16_hak_m15` pushnuto (shoda 35/35) |
| 6 | Šrajer DT + swing (B6) | F17 hotovo: DT OOS +0,07 R (n 74), swing −0,27 R → bez výhody | – (bez výhody, bez kandidátního režimu) |
| 7 | Valchář (OB limitkou, POC) | F18 hotovo: OOS −0,21 R, momentum skóre −0,42 R → bez výhody | – |
| 8 | Kimmel (indexy ICT) | F19 model 2 hotovo: OOS −0,05 R, náhoda +0,09 → bez výhody | – |
| 9 | Obecná strategie uživatele (část A: ranní top-down, SFP s FRVP) | F20 hotovo 2026-11-04: vybraná OOS +0,78 R (n 27), vývoj +0,28 R, rodina OOS kladná / vývoj záporná, SFP+FRVP samo −0,04 R bez nákladů → neověřeno | `F20_user` na MT5 demu (shoda 18/18); do simulátoru ne (Yahoo 1m jen 5 dní) |

**Omezení simulátoru:** Yahoo 1m jen 5 dní, 5m/15m 1 měsíc, 1h 1 rok. Vstup je trhem na zavření svíčky; limit se nahrazuje
signálem na svíčce, která úroveň zasáhne. FM systémy blokuje Risk expozicí měn, kterou zaplní Momentum (export 2026-11-03).

**2026-11-03: Vercel nenasazuje od 2026-10-29** – vyřešeno 2026-11-04: uživatel zveřejnil repozitář (Hobby plán blokoval nasazení z privátního repa), build `5dcc5f0` živě.

**2026-11-04: live na MT5 demu** – `run_fm_demo.py --live` (F12–F16, jen DEMO účet, 0,25 % riziko), viz vault Infrastruktura/FM live test na MT5 demu.

**2026-11-05:** runner v panelu aplikace v noci skončil (bez obchodů); znovu spuštěn v samostatném okně Windows „FM demo live“, log `fm_demo_log.txt`.
