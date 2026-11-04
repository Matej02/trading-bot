# F14 – Pátek: PDF + obrázky jako zdroj, B3 jako dodatek (plán předem, 2026-11-04)

Zdroje:
- celý text 25 PDF (`scratch/fm/patek_vse.txt`);
- všech 80 obrázků (`FM/Obrázky/FM obrázky – Oliver Pátek (scalping).md`, [obr N]);
- Word B3 jen tam, kde PDF mlčí.

## Pravidla
1. **Trend H4** z uzavřených svíček: vyšší pivot high a vyšší pivot low = uptrend [PDF Pivot highs/lows M30, Trend H4, Trading plán].
   Varianta: navíc shoda D1 („H4, DAILY uzavřené svíčky“).
2. **H4 S/R zóna** = aspoň 2 pivoty (high i low, role reversal), které leží blízko sebe (tolerance 0,25 ATR H4), za posledních 300 H4 svíček
   [PDF S/R H4 a H1, obr 27–39; B3 „S/R po 2 dotycích ze swingových bodů, od oka spíš včetně knotů“].
3. **Model A – ve směru H4** [Entry model obr 71–74, PDF Entry model]:
   1. Odmítnutí: pullback dojde do H4 zóny proti směru (short: rezistence nad cenou) v posledních 24 svíčkách.
   2. Nižší high (short) / vyšší low (long) z pivotů M5 nebo M15 (N = 3) [B3 „neobchodovat každý dotyk, chtít LH/HL“].
   3. Close za posledním pivot low / high = vstup trhem na open další svíčky [obr 11 „breakout za market price“].
   4. SL za nižší high + 10 ticků [obr 72, PDF SL zóny].
   5. TP (varianta), vždy RR ≥ 2 (max 5) [PDF TP zóny, obr 11, 71]:
      - `2R`;
      - `pivot`: nejbližší H1 pivot low/high;
      - `zona`: nejbližší protější H4 zóna.
4. **Model B – proti H4 (pullback)** [Entry model obr 75–80; PDF „M5/15 proti trendu H4 (pullback)“]:
   - v H4 downtrendu vyšší low a close nad posledním pivot high = long;
   - TP = nejbližší H4 rezistenční zóna nahoře („highs z levé strany“), RR ≥ 2;
   - SL pod low svíčky před průrazem [obr 75–78].
5. **Session** (Praha, varianta) [PDF Moje strategie „London a NY stock market session“]:
   - `open`: Londýn 9–12 a NY 15:30–18;
   - `full`: Londýn 9–17 a NY 15:30–22.
   Zavřít do 22:00 (intraday). Bez BE [PDF Trading plán]. Vždy jedna pozice.
6. **Trhy** [PDF Úvod]:
   - NAS100 (hlavní), GBPUSD a XAUUSD („občas“);
   - mimo test SPX500, US30 a DAX jako kontrola.
   Data MT5 M1, náklady brokera, vývoj do 2021 (indexy od 2019-02), OOS 2022–26.
7. **Mřížka:**
   - A: 2 (M5/M15) × 2 (session) × 3 (TP);
   - B: 2 × 2;
   - celkem 16 variant.
   Výběr jen na vývoji. Náhoda, bez nákladů, vrstvy (bez odmítnutí, bez LH/HL, + D1).

## Předpoklady
- tolerance zóny 0,25 ATR H4;
- pivot N = 2 (H4, H1) a N = 3 (M5/M15);
- trendline a patterny (trojúhelník, vlajka) nejsou kódem; nahrazuje je LH/HL + průraz pivotu;
- psychologická kulatá čísla nejsou;
- objem průrazu (breakout vs fakeout) není.
