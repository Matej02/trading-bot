---
tags: [grafy]
datum: 2026-11-24
---
# Pohled na grafy 2026-11-24
Rozbor pro výzkum, ne obchodní doporučení. Pravidla viz [[Pohled na grafy (automaticky)]].

## Londýn (08:10)
Signály bota dnes: žádné nové signály ani otevřené obchody; v 06:43 runner zavřel RSI2 SPX500mini časovým výstupem (zavření 23. 11. 7236,17 nad SMA5 7221,42).

| Trh | Můj bias | Bias pravidel | Cíl | Co hlídat |
|---|---|---|---|---|
| EURUSD | short | short | PDL 1.08849 | návrat k NY open / Asie H (1.0914–1.0922) jako sweep, MSS dolů s FVG → short na PDL |
| GBPUSD | short | short | PDL 1.30115 | sweep Asie H 1.30487, pak MSS dolů s FVG → short na PDL |
| XAUUSD | short | short | PDL 3515.40 | rychlý výběr nad NY open 3632 / k Asie H, MSS dolů → short; pod Asie L 3612,6 pokračování |
| NAS100 | long | long | PDH 27137 | sweep Asie L 26707 (pod NY open), MSS nahoru s FVG → long na PDH |
| SPX500 | long | long | PDH 7313.25 | sweep Asie L 7247,5, MSS nahoru s FVG → long na PDH |

### EURUSD
![[2026-11-24_0810_EURUSD.png]]
- Denní: silný sestupný trend, nižší vrcholy; včera velká červená svíčka až k PDL.
- 15m: Asie v úzkém pásmu 1.0905–1.0922, na otevření Londýna cena prolomila Asie L dolů.
- Bias short: trend i struktura dolů, PDL zatím netrefené (~18 pipů).

### GBPUSD
![[2026-11-24_0810_GBPUSD.png]]
- Denní: od 4. 11. jasný pokles, nižší vrcholy, včera zavření u PDL.
- 15m: Asie mírně nahoru (Asie H 1.30487), teď cena právě pod Asie L.
- Bias short, stejně jako EURUSD; cíl PDL ~23 pipů.

### XAUUSD
![[2026-11-24_0810_XAUUSD.png]]
- Denní: dlouhý pokles; včera odraz od ~3510 s horním knotem až k 3691 (PDH), zavření hluboko pod ním.
- 15m: v Asii výběr k 3676 (blízko PDH), pak prodeje pod NY open; cena těsně nad Asie L.
- Bias short: odmítnutí PDH + hlavní trend dolů. Riziko: velké rozpětí (~109) a hluboké zpětné pohyby.

### NAS100
![[2026-11-24_0810_NAS100.png]]
- Denní: trend dolů, ale včera velká býčí svíčka od PDL 25126 až k PDH 27137 – možný obrat/odraz.
- 15m: Asie v pásmu 26707–27036 nad NY open, struktura spíš nahoru.
- Bias long na PDH (~210 bodů). Pozor: denní trend je stále medvědí, jde o protitrendový odraz.

### SPX500
![[2026-11-24_0810_SPX500.png]]
- Denní: podobně jako NAS – po poklesu silná zelená svíčka, zavření blízko PDH.
- 15m: Asie 7247–7298 kolem NY open, cena těsně pod NY open.
- Bias long, cíl PDH jen ~33 bodů nad cenou.

### Průběžné vyhodnocení
- 65 zápisů za 8 obchodních dní (nově 20).
- Claude: n 42, směr 69,0 % (z +2,47), cíl 73,8 %.
- Pravidla: n 59, směr 57,6 % (z +1,17), cíl 64,4 %.
- Claude při neshodě s pravidly: n 12, směr 83,3 %.
- Pravidlo předem: rozhodnutí až po ≥ 30 dnech a ≥ 100 zápisech long/short → zatím nic nevyvozuji.

## New York (14:10)
Signály bota dnes: žádné nové signály ani otevřené obchody; jen v 06:43 časový výstup RSI2 SPX500mini (`<<<`).

| Trh | Můj bias | Bias pravidel | Cíl | Co hlídat |
|---|---|---|---|---|
| EURUSD | neutral | short | PDL 1.08849 | rozpětí dne už vybrané; short jen po sweepu nad ~1.0975 a MSS dolů s FVG, cíl NY open 1.0914 |
| GBPUSD | neutral | short | PDL 1.30115 | totéž: výběr nad 1.3105, MSS dolů → short k Asie H 1.3049; bez toho nic |
| XAUUSD | neutral | short | PDL 3515.40 | pásmo Asie 3613–3677; short po sweepu Asie H a MSS dolů, long jen po sweepu Asie L a MSS nahoru |
| NAS100 | short | long | PDH 27137 | návrat k Asie L 26707 / NY open jako premium, MSS dolů s FVG → short k ~26000 |
| SPX500 | short | long | PDH 7313.25 | návrat k ~7247 (Asie L), MSS dolů s FVG → short k ~7100 |

### EURUSD
![[2026-11-24_1410_EURUSD.png]]
- Denní: trend dolů trvá, ale dnešní svíčka je výrazně zelená.
- 15m: v Londýně sweep Asie L (~1.0900), pak silný růst přes Asie H a NY open až na 1.0966 (≈ 75 pipů, víc než průměrné rozpětí 56).
- Neutral: ranní short nevyšel, struktura dne je nahoru, ale rozpětí je vybrané a denní trend dolů. Proto nesouhlasím s pravidly (short), ale ani long nehoním.

### GBPUSD
![[2026-11-24_1410_GBPUSD.png]]
- Denní: pokles od 4. 11., cena nad včerejším zavřením.
- 15m: stejný obraz jako EUR – sweep Asie L v 8:00, pak ~75 pipů nahoru nad Asie H (rozpětí 66 vybrané).
- Neutral z téhož důvodu; PDH 1.3144 je blízko, ale dojezd po takovém pohybu je nejistý.

### XAUUSD
![[2026-11-24_1410_XAUUSD.png]]
- Denní: dlouhý pokles; včera odraz od PDL, dnes malá svíčka uvnitř včerejšího rozpětí.
- 15m: Asie výběr k 3677, v Londýně sweep Asie L (~3600) a návrat nad NY open, teď 3638 uprostřed pásma.
- Neutral: oba sweepy z rána proti sobě, cena uprostřed. Pravidla chtějí short, souhlasím se směrem trendu, ale bez setupu.

### NAS100
![[2026-11-24_1410_NAS100.png]]
- Denní: hlavní trend dolů, včera velký odraz od PDL; dnes svíčka vrací většinu zisku.
- 15m: v Londýně prolomení Asie L i NY open dolů, nižší vrcholy, cena 26343 (≈ 530 bodů pod NY open).
- Short: struktura je jasně medvědí a cena je pod NY open (discount pro long chybí). Pravidla mají long podle včerejší svíčky – nesouhlasím.

### SPX500
![[2026-11-24_1410_SPX500.png]]
- Denní: stejně jako NAS – včera silná zelená, dnes vracení.
- 15m: pod Asie L 7247 i NY open 7276, nižší vrcholy, cena 7186.
- Short ze stejného důvodu jako NAS; pozor na otevření cash trhu v 15:30, může dát prudký zpětný pohyb.
