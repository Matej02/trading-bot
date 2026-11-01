---
tags: [fm, zdroj, rozcestnik]
zdroj: "D:\\youtube\\FM pdfka"
aktualizovano: 2026-10-29
---
# FM materiály (Funded Mind) – přehled

Kurz **Funded Mind** od uživatele. Původní soubory leží v `D:\youtube\FM pdfka`. Nekopírují se do vaultu, protože mají 180 MB.
**Část 1 („dodatek“) dodána a zpracována 2026-10-29:**
- 314 PDF (1 968 stran) a 28 CSV.
- Text vytažen do `scratch/fm/txt` a zhuštěný korpus po modulech do `scratch/fm/korpus`.
- **Všechny grafy (1 172 obsahových obrázků ve 247 PDF) jsou prohlédnuté.** Zjištění jsou v sekcích „Z grafů v PDF“ u každého autora.
- **Obrázky samotné jsou ve vaultu** (`Přílohy/FM/`, 2026-11-01), galerie po lekcích: [[FM obrázky – Daniel Hvězda (swing)]] · [[FM obrázky – Daniel Valchář (swing)]] · [[FM obrázky – Jan Šrajer (day)]] · [[FM obrázky – Jan Šrajer (swing)]] · [[FM obrázky – Michal Veselovský (day)]] · [[FM obrázky – Oliver Pátek (scalping)]] · [[FM obrázky – Petr Můčka (day)]] · [[FM obrázky – Rafael Kimmel (day)]] · [[FM obrázky – Sunita Hakimi (day)]] · [[FM obrázky – Základy – Likvidita]] · [[FM obrázky – Základy – Price Action]] · [[FM obrázky – Základy – Risk Management]] · [[FM obrázky – Základy – Supply a Demand]] · [[FM obrázky – Základy – Volume]]
  Popisky z grafů (OCR) jsou v `scratch/fm/ocr_vse.txt`, listy s grafy v `scratch/fm/listy/`.
- **Backtest strategií z PDF:** [[F8 Strategie z FM PDF]] (S/D zóny D1/H4/W1, daily bias, makro skóre) – bez výhody.

**Část 2 dodá uživatel.** Doplní se sem a do konceptů.

## Obsah části 1
| Zdroj | Autor, styl | Poznámka |
|---|---|---|
| Základy tradingu (9 modulů + Basecamp + Launchpad) | Jan Šrajer | [[FM Základy tradingu]] |
| Swing: S/D W1+D1, COT, sezónnost | Daniel Hvězda | [[FM Strategie – Daniel Hvězda (swing)]] |
| Swing: fundament + likvidita + OB/volume, H4/D1 | Daniel Valchář | [[FM Strategie – Daniel Valchář (swing)]] |
| Day (4H+M15 S/D + likvidita) a swing (makro skóre) | Jan Šrajer | [[FM Strategie – Jan Šrajer (day + swing)]] |
| Day ICT: daily bias + PO3 + MSS, EURUSD | Michal Veselovský | [[FM Strategie – Michal Veselovský (day, ICT)]] |
| Day: pravděpodobnostní levely, M1/M5 entry | Petr Můčka | [[FM Strategie – Petr Můčka (day, pravděpodobnosti)]] |
| Day: indexové futures NQ/ES, PDH/PDL | Rafael Kimmel | [[FM Strategie – Rafael Kimmel (day, indexy ICT)]] |
| Day: zlato a stříbro, Elliott + Fibo + S/D | Sunita Hakimi | [[FM Strategie – Sunita Hakimi (day, zlato)]] |
| Scalping: Nasdaq, průrazy M5 v trendu H4 | Oliver Pátek | [[FM Strategie – Oliver Pátek (scalping NQ)]] |
| **Data:** historie Trading Analyzer skóre, 28 párů, 2017–2024 | Šrajer | `research_data/fm_score`, viz [[Makro skóre měn]] |

Koncepty z materiálů jsou v [[Databáze konceptů]].

## Co mají autoři společné
1. **Top-down:** směr z HTF (W/D/H4), zóna na HTF, vstup na LTF (M15 → M5/M1). Bez souladu TF se nevstupuje.
2. **S/D zóny a OB jsou na HTF, ne na M1–M15.** M15 slouží jen k upřesnění a M1/M5 jen k načasování.
   F7 to dělalo jinak ([[Supply a demand zóny]]).
3. **Likvidita napřed:** bez sweepu nevstupovat. Cíl je opačná likvidita (PDH/PDL, Asie, swing).
4. **Daily bias** z denní svíčky a obchodování jen v jeho směru (Veselovský, Můčka, Kimmel, Hakimi).
5. **Časová okna:** Londýn ~8–11 a NY ~14–17 CET, Asie je jen akumulace.
6. **Risk:** 0,5–1 % na obchod, RRR ≥ 2 (často 2,5–3), max. 2–3 ztráty denně. Na BE se neshodnou.
7. **Fundament jako filtr:** COT extrémy, sezónnost, DXY, makro skóre. Red news: buď se vyhnout, nebo brát reakci proti zprávě jako manipulaci.

## Kandidáti na test (návrh, pořadí podle poměru cena/přínos)
1. **Daily bias** ([[Daily bias]]). Jen D1 data, tisíce dní, víc trhů.
   Otázka: dosáhne trh po signálu cíle (PDH/PDL) častěji než bez pravidla? Ověří tvrzení „70–80 %“.
2. **Makro skóre** ([[Makro skóre měn]]). Skutečná historie skóre plus D1 ceny z MT5.
   Pravidla „změna ≥ 2 body → směr“ a „bias ±5“ srovnat s náhodou. Vstup až další den (neznáme čas snímku).
3. **S/D zóny podle FM na D1/W1** ([[Supply a demand zóny]]).
   - Hvězda: D zóna uvnitř W zóny, trend 2 HH + 2 HL, lokace v třetinách, limit, SL za zónu, TP protizóna nebo 2R, BE při 1R.
   - Šrajer: unmitigated (≤ 25 %), impulz s BOS, top discount/premium.
   Řeší výtku uživatele k F7.
4. **Intraday ICT model Veselovského** s daily bias filtrem: Asie → sweep pod/nad NY DO → MSS M1/M5 → FVG 0,382 → TP1 Asie, TP2 PDH/PDL.
   Pozor, dílčí prvky byly v F5 a F7 negativní; nový je filtr biasu.
5. **Kimmel na US100/US500:** dotyk PDH/PDL 15:30–18:00 → změna struktury M5 → SL 1,25× → TP interní likvidita.
6. **Pátek na US100 M5:** průraz pivotu ve směru H4 trendu v NY session (pozor na spread).

Méně vhodné: Elliottovy vlny (subjektivní) a fundamentální skóre Valcháře, které nemáme jinak než přes CSV Šrajera.

## Výhrady
- Výsledky autorů (winrate 59 %, bias 70–80 %, payouty) jsou **jejich vlastní tvrzení bez ověření**. Kurz zároveň prodává prop challenge
  a nástroje (Trading Analyzer, TradeZella se slevovým kódem). Tvrzení typu „backtestování ukázalo, že skóre funguje perfektně“ je reklama.
- FM backtestuje ručně (FxReplay, 20–30 obchodů). To je pro závěry málo, viz [[Plán předem]], [[Výběr, kontrola, holdout]] a [[Náhodné vstupy]].
- Objem: mentoři používají futures data. My máme pro forex a zlato jen tick volume → [[Futures data a objem]].
