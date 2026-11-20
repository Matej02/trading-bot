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
