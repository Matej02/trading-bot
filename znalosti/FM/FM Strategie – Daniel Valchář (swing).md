---
tags: [fm, zdroj, strategie, swing]
zdroj: "D:\\youtube\\FM pdfka\\Strategie\\Daniel Valchář - Swing Trading Strategie (PDF)"
zpracovano: 2026-10-29
---
# FM – Daniel Valchář: Swing Trading (fundament + likvidita + OB/volume, H4/D1)

30 PDF, 199 stran. Swing na CFD a futures, hlavně **H4 a D1**. Obchoduje dolarové páry, indexy a zlato, nejraději v NY session.
Vyhýbá se CHF a párům s vysokým spreadem. Udává **winrate 59 %, průměrné RRR 1:2, 1–2 obchody týdně**.
Má FTMO Platinum, přes 50 000 USD výplat. Viz [[FM materiály]].

## Strategie: BIAS → LIKVIDITA → VOLUME/OB → RISK/REWARD → VSTUP
1. **Bias:** fundament je hlavní spouštěč, technika a fundament 50/50.
   - Weekly bias = trend, struktura a COT. Daily bias = struktura D1/H4, denní high/low, OB, FVG.
   - Shoda W a D znamená vysokou pravděpodobnost; **nesoulad = žádný vstup**.
   - Multi-TF: W strategie, D potvrzení, 4H kontext a zóny, 15M exekuce.
2. **Likvidita** → [[Likvidita]]: **vstupuje až po vybrání likvidity** (swing high/low, range, denní/týdenní H/L, session H/L).
   - TP míří na další likviditu: „z likvidity do likvidity“.
3. **Volume / order block:** zóna, kde se potkává objem s nerovnováhou.
   - **OB** = poslední opačná svíčka před impulzem. **Musí způsobit BOS.** → [[Order block]]
   - Sleduje se síla pohybu (rychlost, délka, objem).
   - FRVP přes celý trend nebo korekci: HVN = S/R, LVN = rychlý pohyb, POC = magnet.
     **S/D zóna, která se kryje s POC/HVN, je potvrzená.** → [[Volume profile]]
4. **Vstup:** **limit pouze z předem vyznačené zóny** (Daily a 4H level).
5. **SL** za poslední swing nebo pod OB či volume zónu, nikdy se neposouvá. **TP** na stejný typ zóny (likvidita, OB, volume zóna). RRR 1:1,8–1:3.
6. **Bez BE a bez partials:** „BE ničí statistiku“, používá ho jen ve výjimkách (víkend, zprávy), max. u 5 % obchodů.
7. **Zprávy:** **nikdy nevstupovat 2 h před red news.** Když je cena blízko vstupu, raději zavřít.

## Session levely → [[Killzones a session]]
- **Londýn** (CET):
  - Impulz 09:00–12:00. Session box 09:00–11:30, H/L se sleduje do 17:00.
  - Často tvoří denní high nebo low. Typický scénář: **sweep Asie → trend**.
- **NY** (CET):
  - 14:30–17:00 overlap, nejvyšší volatilita. 14:30 makrodata, 15:30 cash open.
  - Box 15:30–17:30. **NY často retestuje London H/L.**
- Session H/L = zásobník stop lossů → sweep nebo průraz.

## Rating a risk → [[Risk management]]
- **Risk podle ratingu:**
  - A+ = 1,25 %: trend na H4/D1/W1, level potvrzený víc TF, fundament souhlasí, RRR ≥ 1:2.
  - A = 1 %.
  - B = 0,75 %: konsolidace, level bez vyššího TF.
- **Limity:** denně 1–2 %, týdně 3 %. Challenge 2,5 % na obchod, funded 1 %.

## Fundament → [[COT]], [[Sezónnost]], [[DXY a dolar]]
- **COT:** sleduje hlavně non-commercials (velké spekulanty). Rozhodují extrémy, změna v čase a divergence cena–COT.
  Vizualizuje si to v Trading Analyzeru.
- **DXY:** trend a levely DXY jsou bias pro USD páry. Korelace se zlatem a s indexy.
- **Makro:** vyšší inflace → vyšší sazby → silnější měna. Rozhoduje relativní rozdíl měn.
- **Trading Analyzer:**
  - Skóre = inflace, GDP, sazby, sentiment, COT, sezónnost a retail. Sleduje se **momentum skóre**, ne jeho hodnota.
  - Dvě modelové situace: (1) range a skóre se mění → obrat; (2) **divergence** cena–skóre → protitrendový vstup ze silné S/D.
- **Headline risk:** nedržet přes víkend, nepřehánět expozici.

## Testovatelnost
**Střední.** Technická část jde převést do pravidel:
- H4/D1 OB po BOS, překryv s POC/HVN z FRVP, vstup limitem po sweepu likvidity, TP na protilehlou likviditu.
- Zákaz vstupu 2 h před red news.

Fundamentální skóre (Trading Analyzer) nemáme. Nahradit jde COT (CFTC zdarma) a trendem DXY.
Objem je u forexu jen tickový, viz [[Futures data a objem]].

## Z grafů v PDF (prohlédnuto všech 214 obrázků, 2026-10-29)
**Entry model krok za krokem** (z modelového obchodu EURUSD):
1. **Trend D1 nahoru** (HH/HL označené kolečky).
2. **Fundament:** skóre Trading Analyzeru se otáčí nahoru (například z −7 na +2), COT EUR long, retail (DXM) short.
3. **Likvidita:** nad zónou leží řada **rostoucích nebo stejných low** (šikmá linie „xxx“, trendline likvidita).
   Cena tu linii sweepne a dojde do zóny.
4. **Zóna = OB a HVN zároveň:**
   - FRVP se natáhne přes impulzní nohu, od začátku impulzu po jeho vrchol.
   - Zóna je HVN/POC u paty impulzu, tedy poslední svíčky před impulzem (OB, kroužek na grafu).
   - D zóna se zpřesní na 4H.
5. **Vstup:** limit na horní hranu zóny. **SL těsně pod zónou. TP na předchozím high nebo protější likviditě**, RR 1:1,8–3.

**Další poznatky z grafů:**
- **OB:** 1–3 svíčky (poslední opačná a malé svíčky) na swing low přímo před impulzem, který udělal BOS.
  Box se táhne od low po těla. Retest často přijde až po desítkách svíček.
- **Volume zóny:**
  - Profil přes klesající nohu: HVN v horní části = supply pro retest (short).
  - **Thin profile** s jedním HVN nahoře znamená, že retest toho HVN dá silnou reakci.
  - Čáry VAH/VAL/POC z FRVP se prodlouží doprava a cena na ně později reaguje.
- **Supply po vrcholu:** první báze hned po swing high. Retest o několik týdnů později → pokles.
- **Session zóny** (indikátor LuxAlgo Sessions, UTC: Tokyo 23–07, London 07–13:30, NY 13–22):
  sweep high nebo low předchozí seance (růžový box Asie, modrý Londýn) a pak otočka. Šipky na grafech to ukazují v obou směrech.
- **DXY jako potvrzení:** DXY na demand zóně ↔ XAUUSD na supply zóně (short zlata). DXY na vrcholu ↔ EURUSD na dně.
- **Skóre momentum:** GBPCAD skóre 10 → 8 → −1 a cena pak sweepne equal highs a padá.
  EURGBP skóre −1 → +2 a cena sweepne lows a roste. Vstup = změna skóre + sweep likvidity.
- **Zprávy:** 0,74% pohyb na FOMC v řádu minut, proto nevstupovat před red news.
