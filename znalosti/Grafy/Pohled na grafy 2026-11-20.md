---
tags: [grafy]
datum: 2026-11-20
---
# Pohled na grafy 2026-11-20
Rozbor pro výzkum, ne obchodní doporučení. Pravidla viz [[Pohled na grafy (automaticky)]].

## Londýn (08:10)
Signály bota dnes: 07:00 RSI2 SPX500mini long 1,0 lot @ 7138.57, SL 6723.06, TP 11293.7 – provedeno (otevřen, výsledek (TP/SL/čas) v logu není). 07:00 RSI2 US30mini long – neprovedeno (0,091 lotu pod minimem brokera 1,0; min. lot by riskoval 2,76 % účtu).

| Trh | Můj bias | Bias pravidel | Cíl | Co hlídat |
|---|---|---|---|---|
| EURUSD | short | short | 1.09589 (PDL, už trefen) → Asie L 1.09649 | sweep Asie H 1.0991, MSS dolů s FVG → short na Asie L |
| GBPUSD | neutral | short | 1.30820 (PDL, už trefen) | v Asii sweep PDL a odraz; short jen po sweepu Asie H 1.3118 + MSS, jinak stranou |
| XAUUSD | short | short | 3620.60 (PDL, už prolomen) | návrat do 3600–3620 (Asie H / starý PDL), MSS dolů → short na Asie L 3515 |
| NAS100 | short | short | 26436 (PDL, už prolomen) | pullback k PDL 26436 / Asie H 26546, MSS dolů → short pod Asie L 26271 |
| SPX500 | short | short | 7167.75 (PDL, už prolomen) | retest PDL 7168 zespodu, MSS dolů → short pod Asie L 7150 |

### EURUSD
![[2026-11-20_0810_EURUSD.png]]
- Denní: silný sestupný trend od 4. 11., nižší vrcholy; cena mezi PDL a PDH, PDL už dnes trefen.
- 15m: Asie od 1.0965 vystoupala až k Asie H 1.0991 – cena je v prémiové zóně pod PDH.
- Bias short: retracement proti dennímu trendu, čekám sweep Asie H a obrat.

### GBPUSD
![[2026-11-20_0810_GBPUSD.png]]
- Denní: prudký pokles, včerejší svíčka zavřela těsně nad PDL.
- 15m: v Asii sweep PDL i Asie L (1.3082) a pak čistý růst k Asie H 1.3118 – to je spíš býčí vzorec (sweep sell-side, cíl PDH).
- Neutral proti pravidlům: denní trend dolů, ale sweep PDL s odrazem může dát long na PDH 1.3173. Počkat, která strana se v Londýně sweepne.

### XAUUSD
![[2026-11-20_0810_XAUUSD.png]]
- Denní: velmi silný pokles (3 velké medvědí svíčky), cena hluboko pod PDL 3620.
- 15m: v Asii pád až na 3515, teď malý odraz k ~3560 nad NY open 3534.
- Bias short: trend jasný; hlídat odraz do 3600–3620 a tam MSS dolů. Rozpětí je velké (~104), pozor na prudké výkyvy.

### NAS100
![[2026-11-20_0810_NAS100.png]]
- Denní: sestupná struktura, cena pod PDL 26436, nejníž od září.
- 15m: Asie se točila kolem PDL, teď cena u NY open těsně nad Asie L 26271.
- Bias short: PDL prolomen a nevrácen; hlídat retest PDL zespodu.

### SPX500
![[2026-11-20_0810_SPX500.png]]
- Denní: 3 medvědí dny po sobě, cena pod PDL 7168.
- 15m: Asie v úzkém pásmu u PDL, teď u Asie L 7150.
- Bias short podle struktury. Bot má otevřený RSI2 long (jiná, swingová strategie na návrat k průměru) – s intradenním biasem to nesouvisí.

### Průběžné vyhodnocení
45 zápisů za 6 obchodních dní (nově 10). Rozhoduje se až po ≥ 30 dnech a ≥ 100 zápisech long/short – zatím nic nevyvozuji.
- Claude: n 27, směr 51,9 % (z +0,19), cíl 63,0 %
- Pravidla: n 39, směr 56,4 % (z +0,80), cíl 69,2 %
- Claude při neshodě s pravidly: n 6, směr 66,7 %

## New York (16:40)
Signály bota dnes: 07:00 RSI2 SPX500mini long 1,0 lot @ 7138.57, SL 6723.06, TP 11293.7 – provedeno (otevřen, výsledek (TP/SL/čas) v logu není). 07:00 RSI2 US30mini long – neprovedeno (0,091 lotu pod minimem brokera 1,0). Od Londýna nic nového.

| Trh | Můj bias | Bias pravidel | Cíl | Co hlídat |
|---|---|---|---|---|
| EURUSD | neutral | short | 1.09589 (PDL, už trefen) | NY prorazil Asie H 1.0991 nahoru; short jen po sweepu ~1.1003 a MSS dolů pod NY open 1.0983, jinak stranou |
| GBPUSD | neutral | short | 1.30820 (PDL, už trefen) | spike na 1.3125 nad Asie H a návrat; short po MSS pod NY open 1.3108, long po sweepu 1.3095 – zatím nejasné |
| XAUUSD | short | short | 3620.60 (PDL, prolomen) → Asie L 3514.9 | NY zahodil londýnský odraz, cena u NY open 3534; pod ním short na Asie L |
| NAS100 | short | short | 26436 (PDL, prolomen) → nová minima | NY retest PDL 26436 odmítnut, nové minimum ~25950; short na odrazu k ~26200 |
| SPX500 | short | short | 7167.75 (PDL, prolomen) → nová minima | sweep Asie H 7192 v NY a prudký pád; short na odrazu pod PDL/NY open 7156 |

### EURUSD
![[2026-11-20_1640_EURUSD.png]]
- Londýn: sweep Asie H 1.0991 a pád pod Asie L na ~1.0962 (londýnský short z ranního plánu vyšel).
- NY: silný růst přes NY open i Asie H až na 1.1003, teď 1.0996 – vnitrodenní struktura býčí.
- Neutral proti pravidlům: denní trend dolů, ale NY ukázal displacement nahoru; směr na zbytek dne nejistý.

### GBPUSD
![[2026-11-20_1640_GBPUSD.png]]
- Od sweepu PDL v Asii vyšší minima; Londýn i NY drží 1.309–1.312.
- NY spike na 1.3125 nad Asie H a návrat pod něj – možný sweep buy-side, ale bez jasného MSS.
- Neutral (jako ráno): denní trend dolů vs. vnitrodenní růst od PDL.

### XAUUSD
![[2026-11-20_1640_XAUUSD.png]]
- Londýn odrazil k ~3585, NY odraz prodal a cena spadla zpět k NY open 3534.
- Denní: 3. velká medvědí svíčka, hluboko pod PDL. Bias short, další cíl Asie L 3515.
- Rozpětí ~104 bodů – i odraz o 50 bodů je normální šum.

### NAS100
![[2026-11-20_1640_NAS100.png]]
- Londýn i ranní NY dělaly nižší minima pod Asie L 26271.
- NY spike přesně k PDL 26436–26500 a prudké odmítnutí na nové minimum ~25950 (učebnicový retest zespodu).
- Bias short, cena nejníž od září.

### SPX500
![[2026-11-20_1640_SPX500.png]]
- NY spike nad Asie H 7192 (sweep buy-side) a pád pod Asie L na ~7130.
- Bias short. Bot drží RSI2 long @ 7138.57 (swingová strategie na návrat k průměru) – cena je teď těsně pod jeho vstupem, s intradenním biasem to nesouvisí.
