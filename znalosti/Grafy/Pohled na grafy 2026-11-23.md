---
tags: [grafy]
datum: 2026-11-23
---
# Pohled na grafy 2026-11-23
Rozbor pro výzkum, ne obchodní doporučení. Pravidla viz [[Pohled na grafy (automaticky)]].

## New York (13:00)
Signály bota dnes: žádné (v `fm_demo_log.txt` není k 13:00 žádný řádek s dnešním datem, ani start runneru).

Ranní běh (Londýn) dnes poznámku nezaložil, proto tu chybí i průběžné vyhodnocení.

**Pozor na data:** u EURUSD a GBPUSD vyšlo PDH = PDL (jedna hodnota). Předchozí „den“ je nejspíš jen krátký nedělní kousek svíčky, ne pátek. Cíl pravidel u forexu je proto podezřelý. U zlata a indexů je Asie L dána jedním osamoceným knotem kolem 5:00 (pravděpodobně chybný tik ve futures), skutečné minimum Asie je výš.

| Trh | Můj bias | Bias pravidel | Cíl | Co hlídat |
|---|---|---|---|---|
| EURUSD | short | short | pátek low ~1.0955 | návrat k NY open / Asie L 1.098, odmítnutí, MSS dolů s FVG → short |
| GBPUSD | short | long | pátek low ~1.3075 | pullback k Asie L / NY open 1.3105–1.311, MSS dolů → short; long jen po sweepu 1.3075 a MSS nahoru |
| XAUUSD | neutral | short | PDH 3638 / NY open 3607 | sweep PDH 3638, pak MSS dolů s FVG → short; nebo pád pod NY open 3607 |
| NAS100 | long | short | PDH 26603 | sweep pod NY open 25842 / Asie H 25945, MSS nahoru s FVG → long na PDH |
| SPX500 | long | short | PDH 7216 | sweep pod Asie H 7104 / NY open 7085, MSS nahoru → long na PDH |

### EURUSD
![[2026-11-23_1300_EURUSD.png]]
- Denní: silný sestupný trend, nižší vrcholy i dna, cena u minim (~1.096).
- 15m: Asie šla nahoru, Londýn vzal Asie H (1.1005) a pak spadl pod Asie L, NY open i „PDL“ – klasický Judas swing nahoru a pokračování dolů.
- Bias short souhlasí s pravidly; cíl pravidel je kvůli chybě dat už „trefen“, reálný cíl je páteční low.

### GBPUSD
![[2026-11-23_1300_GBPUSD.png]]
- Denní: sestupný trend od 5. 11., pátek malá zelená svíčka u minima.
- 15m: stejný vzor jako EUR – Londýn sweep Asie H (~1.3135) a pád pod Asie L a NY open.
- Nesouhlasím s pravidly (long): long vychází z malé páteční svíčky a chybného PDH/PDL, struktura na 15m i denní je dolů.

### XAUUSD
![[2026-11-23_1300_XAUUSD.png]]
- Denní: prudký pád, ale pátek odmítl PDL 3503 dlouhým knotem a zavřel výš.
- 15m: Asie skočila nahoru, Londýn došel těsně pod PDH 3638 a teď se cena drží v pásmu 3607–3635.
- Neutral: dlouhodobě short, krátkodobě odraz – čekám, jestli NY vezme PDH a otočí (short), nebo ho prorazí.

### NAS100
![[2026-11-23_1300_NAS100.png]]
- Denní: sestupný trend, ale pátek velká býčí svíčka od PDL 24976 zpět nad 26000.
- 15m: od pátku vyšší dna, dnes průraz nad Asie H a NY open, cena drží nad nimi.
- Nesouhlasím s pravidly (short): cíl PDL je o ~1050 bodů níž (celé denní rozpětí), struktura dne je nahoru, bližší likvidita je PDH 26603.

### SPX500
![[2026-11-23_1300_SPX500.png]]
- Denní: stejné jako NAS – trend dolů, pátek silné odmítnutí PDL 6898.
- 15m: průraz Asie H 7104 v Londýně, vyšší dna, cena 7137.
- Long na PDH 7216 ze stejného důvodu jako u NAS; short až po MSS zpět pod NY open.

## New York (14:10)
Signály bota dnes: žádné (v `fm_demo_log.txt` žádný dnešní řádek se SIGNAL, `>>>`, `--- neprovedeno` ani `<<<`).

Druhý běh v relaci NY (po 13:00). Chyba dat u forexu trvá: PDH = PDL u EURUSD (1.09745) i GBPUSD (1.30818), cíl pravidel „trefen“ je proto nespolehlivý.

| Trh | Můj bias | Bias pravidel | Cíl | Co hlídat |
|---|---|---|---|---|
| EURUSD | short | short | další nízko pod 1.0935 | pullback k 1.0955–1.097, MSS dolů s FVG → short; pozor, pohyb už je natažený |
| GBPUSD | short | long | 1.3065 a níž | návrat k 1.3082–1.310, odmítnutí → short; long jen po MSS nahoru nad 1.310 |
| XAUUSD | neutral | short | PDH 3638 / NY open 3607 | sweep PDH 3638 a MSS dolů → short; ztráta 3607 → short na 3575 |
| NAS100 | long | short | PDH 26603 | cena je v zóně NY open 25842 – Asie H 25945; sweep pod NY open a MSS nahoru s FVG → long |
| SPX500 | long | short | PDH 7216 | test Asie H 7104 / NY open 7085; MSS nahoru → long; zavření pod 7085 ruší long |

### EURUSD
![[2026-11-23_1410_EURUSD.png]]
- Od 13:00 další pád, nové minimum knotem ~1.0935, cena 1.0942.
- Struktura 15m i denní dolů, short souhlasí s pravidly; bez pullbacku je vstup pozdě.

### GBPUSD
![[2026-11-23_1410_GBPUSD.png]]
- Cena prošla pod „PDL“ 1.3082 a páteční minimum, knot ~1.3068, teď 1.3075.
- Pravidla (long) dál vycházejí z chybné nedělní svíčky; struktura je dolů.

### XAUUSD
![[2026-11-23_1410_XAUUSD.png]]
- Beze změny: úzké pásmo 3607–3630 pod PDH 3638.
- Neutral do rozhodnutí v killzone.

### NAS100
![[2026-11-23_1410_NAS100.png]]
- Od 13:00 návrat z ~26000 na 25928, tedy do zóny Asie H / NY open, kterou jsem hlídal.
- Long platí jen při reakci v této zóně; pád pod Asie L by ho zrušil.

### SPX500
![[2026-11-23_1410_SPX500.png]]
- Pokles ze 7137 na 7104 = test Asie H shora, NY open 7085 těsně pod.
- Stejná logika jako NAS: long po sweepu a MSS nahoru, jinak neutral.
