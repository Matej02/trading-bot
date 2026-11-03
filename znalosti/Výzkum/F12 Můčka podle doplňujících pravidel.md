---
tags: [vyzkum, f12, fm]
datum: 2026-11-03
---
# F12 – Můčka podle doplňujících pravidel uživatele

Zadání: po [[Doplňující pravidla k FM PDF|doplňujících pravidlech]] (3. 11. 2026) testovat znovu, a to co nejvěrněji.
Postup podle nového pravidla „před testem projít vše“:
- celý text Petrových PDF (26 lekcí);
- všech **196 obrázků** [[FM obrázky – Petr Můčka (day)|jeho galerie]];
- navazující Základy: [[FM obrázky – Základy – Price Action|Price Action]] (32), [[FM obrázky – Základy – Likvidita|Likvidita]] (12),
  [[FM obrázky – Základy – Supply a Demand|S&D]] (136), [[FM obrázky – Základy – Volume|Volume]] (49).

Plán předem je v `F12_PLAN.md`. Kód:
- `research_f12_ms.py`: struktura;
- `research_f12.py`: strategie;
- `research_f12_eval.py`: vyhodnocení;
- `research_f12_vrstvy.py`: vrstvy konceptů.

Výstupy jsou v `research_data/f12/`.

## Co z obrázků upřesnilo pravidla
- **Strong/weak a BOS** (MS teorie s5–s6, Trend s3–s4): BOS čárkovaně od swingu po svíčku průrazu, S-High/S-Low = extrém
  mezi nimi, W-Low/W-High = extrém po průrazu. Interní struktura (I-BOS, I-Low) je uvnitř pullbacku.
- **Entry model** (Entry model s3, s4, s9):
  - cena vybere low v zóně;
  - MSS = close nad posledním lower high, což je na nižším TF změna struktury přes strong level;
  - vstup na 0,618–0,66 nohy od sweepu k vrcholu po MSS, na 5m do FVG;
  - SL přímo pod low sweepu, TP ~3 R.
- **25 % zóny** (Základy S&D s4-2, popisek na grafu): „Jakmile je jednou více jak 25 % zóna vyplněná, následující dotek už je nevalidní“.
  První dotek platí, i když jde hluboko.
- **Platné zóny jen ty, které udělaly BOS** (S&D s3–s4, ✓/✗). Zóny v pomalém driftu bez BOS jsou přeškrtnuté.
- **Top-down** (MS teorie s7): denní trend → 4H → 15m → vstup na 5m/1m.

## Jak je to v kódu
- **Struktura:**
  - BOS = close tělem o ≥ 0,1 ATR za weak levelem;
  - momentum: tělo ≥ průměr 20 těl a ≤ 3 ATR, další svíčka nezavře zpět a má objem nad MA50 nebo stejnou barvu;
  - weak se potvrdí pullbackem ≥ 0,35 nohy.
  - **„Fibo se přesune na další bod“**: bez toho by struktura zamrzla (EURUSD 2022 spadl 1,23 → 0,95 bez pullbacku 38 % celé nohy).
    Kotva Fibo se proto posouvá na poslední swing ZigZagu na zavíracích cenách (otočka k × ATR).
- **POI:**
  - zóna u strong levelu BOS na 4H (platí 30 dní) a 15m (5 dní), base z malých svíček (max 6), hranice přes těla;
  - balanční level = první návrat na úroveň BOS.
- **Vstup:**
  - killzone 9–11 a 13:30–17 pražského času; daily bias ze včerejší svíčky; 4H trend s BOS do 30 dní;
  - na 5m/1m: sweep v POI → změna struktury → limit 0,618 (+spread) nebo 50 % FVG;
  - SL na sweepu, min. 6 a max. 15 pipů (jinde přes ATR D1);
  - TP buď 2,5 R, nebo nejbližší nedotčený pravděpodobnostní level ≥ 2 R (PDH/PDL, Asia H/L, VWAP a POC včerejška);
  - konec dne 22:00, max 2 obchody denně.
- **Data:** MT5 M1 s náklady brokera ([[Náklady brokera]]), vývoj do 2021, OOS 2022–2026.
  Trhy EURUSD, GBPUSD, XAUUSD, XAGUSD, NAS100.

## Kontrola struktury na grafu (pro uživatele)
![[F12 struktura EURUSD 4H (k=1,5, 2025).png]]
![[F12 struktura EURUSD 15m (k=1,5, 2025).png]]
- Na 15m drží hlavní struktura downtrend i při rally o 220 pipů, protože strong high leží výš. To je podle pravidel (Petrův obr. s6-1),
  uvnitř by šla interní struktura.
- **Velikost swingu (k) je odhad.** Uživatelovy screenshoty 6E 15m ve vaultu nejsou.

## Výsledky (s náklady brokera, OOS 2022–2026)
**Plná pravidla, mřížka 72 variant** (k × POI × 5m/1m × GP/FVG × TP), 1 577 obchodů, jen ~22 na variantu za 9 let:
- nejlepší na vývoji `k=1,5, POI zóna i balanc, vstup 1m GP 0,618, TP 2,5 R`: vývoj **−0,18 R** (n 97), OOS **+0,06 R** (n 98);
- náhoda se stejným SL/TP, časem a směrem: −0,21 / −0,08 R;
- bez nákladů +0,22 R OOS vs náhoda −0,13 R, ale vývoj −0,04 R.
- **Prahy nesplnila žádná varianta.**

**Vrstvy konceptů** (1m, k = 1,5, 5 trhů):

| Vrstva | vývoj | OOS | náhoda OOS | bez nákladů OOS |
|---|---|---|---|---|
| 0 jen MSS v killzone + GP 0,618 | −0,31 R (n 2 913) | −0,20 R (n 2 722) | −0,16 R | 0,00 R |
| 1 + 4H struktura | −0,25 R (1 120) | −0,22 R (1 316) | −0,12 R | −0,03 R |
| 2 + daily bias | −0,22 R (608) | −0,20 R (708) | −0,20 R | +0,01 R |
| 3 + POI zóna | −0,21 R (79) | −0,11 R (82) | −0,15 R | +0,04 R |
| 3b + POI balanční level | −0,21 R (21) | +0,81 R (21) | −0,05 R | +0,85 R |
| 3c + POI obojí (plná pravidla) | −0,18 R (97) | +0,06 R (98) | −0,15 R | +0,22 R |

Závěry z vrstev:
- **Samotný entry model (MSS + 0,618) je bez nákladů přesně na nule.** S náklady ztrácí ~0,2 R, protože stop 6–12 pipů je z velké části spread.
- **4H struktura ani daily bias nic nepřidávají**, výsledek se jen zmenší.
- POI zlepší OOS, ale na vývoji ne a vzorky jsou malé. Balanční level má OOS +0,81 R jen z 21 obchodů, na vývoji −0,21 R.

**NAS100 – vypadalo to dobře, ale neopakuje se:**
- Plná pravidla: vývoj +0,66 R (n 20), OOS +0,78 R (n 24). 4H + POI bez biasu: +0,45 R (48) a +0,17 R (76).
- **Kontrola na indexech, které v testu nebyly:**
  - S&P 500 v OOS −0,47 R (n 22), přestože s Nasdaqem silně koreluje;
  - Dow −0,27 R (25), DAX +0,10 R (14);
  - tři indexy dohromady −0,00 R, náhoda +0,01 R.
- Trh byl vybraný až po pohledu na výsledky, takže jde o náhodu z mnoha porovnání.

![[F12 Můčka – ukázky obchodů NAS100 (OOS).png]]
![[F12 Můčka – ukázky obchodů GBPUSD (OOS).png]]

## Závěr
- Ani s doplňujícími pravidly (struktura tělem s momentem, strong/weak po 0,382, zóny jen s BOS a 25 %, první návrat na BOS,
  killzones, daily bias, 4H trend, sweep → MSS → 0,618/FVG, SL na sweepu, TP na pravděpodobnostních levelech) nemá Petrova
  strategie na datech výhodu nad náhodou.
- Entry model sám je mince; konfluence ubírají obchody, ale nezlepšují je.
- Potvrzuje to [[F10 Entry modely mentorů FM|F10]] a [[F11 Mentoři FM znovu a podrobně|F11]] a zápis v [[Co nefunguje]].

Co z materiálu nešlo přesně převést, a proto může test být jiný než Petrovo ruční obchodování:
- velikost swingu;
- výběr „kvalitní“ zóny okem (A+/A/B rating);
- footprint a absorpce (nemáme data);
- jeho rozhodnutí 1m vs 5m podle kvality setupu.
