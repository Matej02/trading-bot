---
tags: [vyzkum, plan]
datum: 2026-11-20
---
# F63 a F64: den před svátkem v Evropě a hodiny bitcoinu

Zadání uživatele (2026-11-20): „Ano, dej A do simulátoru a pokračuj dalšími testy.“ Bot ani runner se nemění. Plán je zapsaný **před výpočtem**, pravidla se po výsledku nemění.

**Proč tyhle dva:**
- **F63:** kalendářní jevy v Evropě vydržely po 2019 líp než v USA (přelom měsíce, [[F61 a F62 Ověření kandidátů (přelom měsíce v Evropě, zlato v Asii)|F61]]). Den před svátkem v USA ([[Fronta nápadů F35–F39|F37]]) neprošel jen kvůli vývoji 1990–2018; Evropa je nezávislý vzorek.
- **F64:** krypto obchoduje nonstop a toky podle regionů (Asie, Evropa, USA) se v hodinách dne liší. Jiná třída než všechno dosud testované. Okno se nevybírá od oka, ale **na vývoji 2019–2021** a ověřuje se na letech, která se při výběru neviděla.

## F63 Den před svátkem v Evropě: plán
- **Trhy:**
  - DAX, FTSE 100, CAC 40, Euro Stoxx 50, IBEX 35;
  - Yahoo denní (`f6_*_1d.pkl`) 1990–2026;
  - broker H1 → denní 2019–2026.
- **Den před svátkem P:** obchodní den, po kterém následuje pracovní den (po–pá), kdy burza v datech Yahoo neobchoduje. Mezera 1–2 pracovní dny; delší výpadky dat se nepočítají. Svátky se tedy berou z dat každého trhu, ne z kalendáře.
- **Obchod:** long od zavření dne P−1 do zavření dne P (jako F37). Broker se vyhodnocuje ve stejné dny P podle Yahoo.
- **Náklady:**
  - půl spreadu brokera na vstupu i výstupu;
  - swap za noc (středa 3×).
  - R = výsledek / ATR20.
- **Srovnání:** stejný obchod zavření → zavření ve všech ostatních dnech. Převis = průměr R ve dny P − průměr ostatních dní, Welch t, po dnech (průměr přes trhy).
- **ANO jen když platí vše:**
  1. Vývoj (Yahoo 1990–2018): signál > 0, převis > 0, t ≥ 2,0.
  2. Kontrola (Yahoo 2019–2026): signál > 0, převis > 0, t ≥ 1,5.
  3. Broker 2019–2026: signál > 0 a převis > 0.
  4. Převis kladný aspoň v 55 % let.
  5. Nezávislost na F61: bez dnů P, které padnou do okna přelomu měsíce (poslední den měsíce až 3. den dalšího), převis > 0 (celé období Yahoo).
- **Popis navíc (nerozhoduje):** počet dnů P za rok a trh, výsledek podle trhů.

## F64 Hodiny bitcoinu: plán
- **Data:**
  - Binance BTCUSDT 1h (UTC) 2019–2026, hlavní zdroj;
  - broker BTCUSD H1 2022–2026 (čas jako v F58, +1 h v britském letním čase), druhý zdroj;
  - ETH: Binance ETHUSDT 1h 2022–2026.
- **Obchody:**
  - 4hodinová okna začínající v každé celé hodině UTC (24 oken), long i short (48 možností);
  - R = výsledek / denní ATR20 (dny UTC).
- **Náklady:**
  - spread brokera podle hodiny (BTC ~24 $, ETH ~2,8 $), polovina na vstupu i výstupu;
  - swap brokera, pokud okno přechází půlnoc Londýn.
- **Srovnání:** všechna ostatní 4h okna stejného dne ve stejném směru. Převis = signál − srovnání, Welch t, po dnech.
- **Výběr (jen vývoj 2019–2021):** okno a směr s nejvyšším t převisu. Jiné se pak nezkoušejí.
- **ANO jen když platí vše:**
  1. Vývoj 2019–2021: vybrané okno t ≥ 3,0. Laťka je vyšší, protože se vybíralo ze 48 možností.
  2. Kontrola Binance 2022–2026: signál po nákladech > 0, převis > 0, t ≥ 1,5.
  3. Broker 2022–2026: signál po nákladech > 0 a převis > 0.
  4. ETH Binance 2022–2026, stejné okno a směr: převis > 0.
  5. Převis kladný aspoň v 55 % let (2019–2026, Binance).
- **Popis navíc (nerozhoduje):** profil průměrného výnosu podle hodiny UTC ve vývoji i kontrole.

Skript `scratch/f63_f64.py`, výstup `research_data/f63/souhrn.txt`.

## Výsledky (2026-11-20)
Souhrn: `research_data/f63/souhrn.txt`.

**F63 den před svátkem v Evropě: BEZ VÝHODY**

| Bod | Výsledek |
|---|---|
| 1) vývoj 1990–2018 | signál +0,052 R, převis +0,063, t 1,88 → **NE** |
| 2) kontrola 2019–2026 | signál −0,005 R, převis +0,002, t 0,03 → **NE** |
| 3) broker 2019+ | signál −0,025 R, převis −0,018 → **NE** |
| 4) roky | 59 % kladných → ano |
| 5) bez dnů přelomu měsíce | převis +0,070 → ano |

- Podle trhů (celé období): FTSE převis t 2,65, CAC 1,99, IBEX 1,80, EuroStoxx 0,99.
- Stejný vzorec jako jinde: do 2008 silné, od 2010 kolem nuly. Jev se vytratil, F37 v USA ani Evropa ho dnes nenesou.

**F64 hodiny bitcoinu: BEZ VÝHODY**
- Vybráno na vývoji 2019–2021: short 02:00–06:00 UTC, převis t 2,51 (laťka 3,0 → NE).
- Kontrola Binance 2022–2026: převis −0,003 (t −0,45). Broker 2022+ převis 0,000. ETH −0,002.
- **I 10 nejlepších 4h oken z vývoje je po nákladech záporných** (−0,02 až −0,05 R). Spread brokera ~24 $ sní celý typický pohyb za 4 hodiny.
- Profil hodin ve vývoji (např. 21:00 UTC +10 bp) se v kontrole neopakuje: 21:00 +1,2 bp, nejvyšší 22:00 +3,4 bp.
- **Závěr:** krátké obchody na kryptu u tohoto brokera nedávají smysl. Hodinové vzorce jsou malé a nestálé.

Počet testů od F35: 32, prošly 2 (F42, F52).

