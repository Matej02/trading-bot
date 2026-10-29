---
tags: [fm, zdroj, strategie, scalping]
zdroj: "D:\\youtube\\FM pdfka\\Strategie\\Oliver Pátek - Scalping & Intraday Strategie (PDF)"
zpracovano: 2026-10-29
---
# FM – Oliver Pátek: Scalping a intraday (Nasdaq futures, průrazy M5 v trendu H4)

25 PDF, 169 stran. Obchoduje **Nasdaq futures** (občas GBPUSD a XAUUSD) v Londýnské a NY stock session.
Payouty Topstep 22 000 USD, Take Profit Trader 9 596 a 3 341 USD. „Trend is your friend.“ Viz [[FM materiály]].

## Strategie (entry model)

| TF | Co sleduje |
|---|---|
| **D1/H4** | trend (uzavřené svíčky), trendline, **S/R zóny H4** |
| **H1/M30** | zóny z highs/lows, trendline |
| **M30** | svíčkové formace a patterny (trojúhelníky, vlajky) |
| **M15/M5** | **vstup po průrazu pivot high/low** (breakout) |

- Obchoduje **M15/M5 trend v H4 trendu**, nebo M15/M5 proti H4 trendu jako pullback.
  V uptrendu na H4/D1 nebere shorty, s výjimkou krátkého pullbacku jako přípravy na long.
- **Pivot high/low:** svíčka vyšší (nižší) než svíčky vlevo i vpravo.
  **Průraz M5 pivot high = long, průraz pivot low = short.**
- **Trendline:** proražení s udržením za čarou znamená změnu trendu; odraz znamená pokračování.
  **Breakout vs fakeout:** breakout má vyšší objem a silnou price action, fakeout slabý objem a návrat.
  Na nízkých TF je hodně fakeoutů, proto potvrzení na pullbacku.
- **SL** za S/R, za svíčkovou formaci nebo za trendline. **TP** na S/R, pivot nebo cíl patternu. RRR 2:1–3:1.
- **Pravidla:**
  - Risk na challenge až 2 %, na funded max. 1 %.
  - **Žádný BE**: „vstupuji a jsem ochoten vzít ztrátu“.
  - Bez konfluence neobchoduje. Po dosažení denního profitu **lockout** (Topstep).
- **Scaling:** přidávání kontraktů ve směru zisku (pyramidování).
- **Fundament pro NQ:** earnings velkých technologických firem (AAPL, MSFT, NVDA, GOOGL, META, AMZN), Fed, CPI, GDP a nezaměstnanost.

## Souvislost s naším výzkumem
Je to **trendový průraz** se zónovým kontextem, příbuzný [[Průraz F2 (proraz_d1)]], který funguje na D1.
Na nízkých TF jsme průrazy zkoušeli v [[F4 Vstup na menším timeframu]] a výsledek byl negativní kvůli nákladům.
Kandidát na test: **US100 na M5**, průraz pivotu ve směru H4 trendu (EMA nebo struktura), jen session NY.
Pozor na náklady: spread US100 u brokera, viz [[Náklady brokera]].

## Z grafů v PDF (prohlédnuto všech obrázků, 2026-10-29) – entry model mechanicky
**Short v H4 downtrendu** (popisky přímo z grafů):
1. **Odmítnutí:** cena dojde k rezistenci, tedy k H4 zóně nebo H4 trendline (zelený box).
2. **Vytvoření nižšího high** na M5/M15.
3. **Průraz low** (pivot low M5) = vstup short.
4. **TP na pivot low** (předchozí low níž, zelená linka). SL nad nižší high nebo nad svíčku průrazu.

RR na obrázcích ~2:1.

**Long po průrazu patternu** (protitrendově k H4):
1. Průraz patternu (trojúhelník nebo vlajka na M5).
2. Průraz highs patternu.
3. **TP na highs z levé strany** (předchozí H4 high nebo zóna).
4. **SL pod předešlou svíčku průrazu.**

**Další grafy:**
- **Pivot highs/lows M30:**
  - Boxy kolem lokálních vrcholů a den. Při průrazu pivot low směrem dolů vstup short, SL nad pivot high, RR 2,1
    (příklad NQ: SL 16,75 bodu, TP 35,25 bodu).
- **SL zóny:** SL nad rezistencí, pod svíčkovou formací nebo nad trendline v downtrendu. TP na S/R zónu.
- **S/R flip:** po průrazu a potvrzení se rezistence mění v support (kroužky). Cena se vrací na retest a pokračuje.
- **Fakeout v kanálu:** cena prorazí kanál, ale vrátí se zpět. Teprve break out s retestem znamená změnu trendu.
  „Poslední high před průrazem“ je spouštěč.
- **Multičasová analýza NQ:** D1 downtrend (trendline), na M30 boxy uptrendu v downtrendu = pullbacky na short.
- Svíčky: doji, hammer, engulfing a hanging man na M5 v zóně (zelené boxy).

## Otestováno – F10 (2026-10-29)
Entry model přesně podle PDF na minutových datech, OOS 2022–26: **−0,05 R (n 2 868), NQ −0,01 R**, bez výhody. → [[F10 Entry modely mentorů FM]]
