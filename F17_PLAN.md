# F17 – Šrajer (day + swing): PDF + obrázky jako zdroj, B6 jako dodatek (plán předem, 2026-11-04)

Zdroje:
- celý text 9 (DT) a 24 (swing) PDF (`scratch/fm/srajer_vse.txt`);
- všech 18 + 71 obrázků (galerie Jan Šrajer day/swing, [obr N]);
- B6 jen jako dodatek („MS + S/D, volume profile jako filtr“).
- Šrajer DT byl v F11 (−0,14 R). Nové jsou body z obrázků entry modelů a celý swing.

## A) Day trading [PDF Můj obchodní styl, Entry Model, Ranní analýza; obr DT 2, 5, 14–16]
1. TF 4H / 15m / 5m. Trhy EURUSD a XAUUSD, „většina forexu“ → i GBPUSD, AUDUSD, USDJPY, USDCAD jako kontrola.
2. Bias = 4H struktura (trend z pivotů) + **premium/discount** 4H swingu (long jen pod 0,5) [Entry model, obr 15 „0,5 Fibo“].
3. **4H S/D zóna** ve směru, v ní **15m S/D zóna** (FM pravidla: impulz s BOS, mitigace ≤ 25 %).
4. **Likvidita před dotekem** (varianta) [obr 14–16]:
   - `eq`: equal lows/highs – 2 pivoty 15m do 0,1 ATR 15m;
   - `piv`: pivot low (swing N 3);
   - cena ji vybere těsně před dotekem zóny / v ní.
5. **Vstup** (varianta):
   - `limit` na proximal 15m zóny;
   - `shift`: lokální změna trendu na 5m (close za posledním 5m pivotem) po sweepu v zóně → vstup trhem [obr 16 „Lokální změna trendu → retest demandu“].
6. **Okna** 8:30–9:30, 10:30–11:30, 13:30–16:00 Praha [PDF]. Asie ne.
7. **SL** za distal 15m zóny (nebo extrém sweepu, co je dál).
   **TP** 2,7 R (průměr TP1/TP2), varianta protější 15m zóna (RR 2–3,5). RR < 2 se nebere [PDF]. Konec dne 22:00.

## B) Swing [PDF S/D swing, Refinements, Score overview, Set and forget; obr swing 2–8, 59–63]
1. **HTF D1, LTF 4H** („dny → týdny: týdenní / D1“, za nás ideální D1 → 4H) [PDF S/D, tabulka TF].
2. Nejbližší **unmitigated** D1 supply nad cenou a D1 demand pod cenou (impulz s BOS, mitigace ≤ 25 %).
3. **Lokace** = Fibo 0,333 / 0,5 / 0,666 mezi spodkem supply a vrchem demand.
   Long jen v **top discount** (v demand zóně, pod 0,333), short v top premium [obr 4–8].
4. Vstup **limit** na proximal 4H zóny uvnitř D1 zóny (varianta), nebo na proximal D1 zóny („set and forget“).
5. **SL** za distal, **TP** 2R („stačí 2R/R trade“, obr 6–7) nebo varianta 0,5 rovnováha / protější zóna. Nejdéle 20 dní, bez BE.
6. **Fundament – skóre Trading Analyzer** (historie 28 párů 2017-01 až 2024-10 v `research_data/fm_score`), varianty:
   - `0` bez filtru;
   - `bias`: skóre ≥ +5 pro long, ≤ −5 pro short [Score overview „bullish +5..+8, very +9..+18“];
   - `zmena`: změna skóre za 5 dní ≥ +2 pro long, ≤ −2 pro short [„relativní změny skóre mají větší význam“].
   Skóre z dne D se použije od dne D+1.
7. **Trhy:** 28 párů se skóre (H1 data MT5).
   Vývoj 2017–2021, OOS 2022–2024-10 (skóre končí 2024-10-03); bez skóre i OOS 2022–2026.

## Předpoklady
- equal highs = do 0,1 ATR 15m;
- 25 % = close 15m/4H za čtvrtinou hloubky;
- zóna z find_zones (F8);
- skóre se bere jako denní uzavřené.
