---
tags: [grafy]
datum: 2026-11-17
---
# Pohled na grafy 2026-11-17
Rozbor pro výzkum, ne obchodní doporučení. Pravidla viz [[Pohled na grafy (automaticky)]].

## Londýn (08:09)
Signály bota dnes: žádné (v logu dnes žádný SIGNAL, otevřený ani zavřený obchod).

| Trh | Můj bias | Bias pravidel | Cíl | Co hlídat |
|---|---|---|---|---|
| EURUSD | neutral | short | PDL 1.09938 (už trefen) | po sweepu PDL/Asie L odraz; short jen po MSS pod NY open 1.1007 |
| GBPUSD | neutral | short | PDL 1.31782 (už trefen) | sweep Asie L a PDL, odraz k Asie H; short až po MSS |
| XAUUSD | short | short | PDL 3835.20 | sweep Asie H 3889.6 a návrat pod NY open 3877.6 → short na PDL |
| NAS100 | short | short | PDL 27234.75 (trefen) | cena na PDL/Asie L; sweep dolů a MSS nahoru by obrátil bias |
| SPX500 | short | short | PDL 7420.25 | cena u PDL; po sweepu Asie L 7414.75 hlídat odraz |

### EURUSD
![[2026-11-17_0809_EURUSD.png]]
- Denní: silný pokles, cena kolem PDL; cíl pravidel už trefen.
- Asie: sweep Asie L i PDL, ostrý odraz nad NY open a k Asie H.
- Neutral, protože sweep proběhl a odraz jde proti dennímu trendu; na straně shortu chybí MSS.

### GBPUSD
![[2026-11-17_0809_GBPUSD.png]]
- Denní: pokles z vrcholů, cena na PDL.
- Asie: sweep Asie L pod PDL, odraz těsně pod Asie H.
- Neutral – nesouhlasím s pravidly (short), cíl PDL už je trefen a likvidita dole sebrána.

### XAUUSD
![[2026-11-17_0809_XAUUSD.png]]
- Denní: dlouhý pokles, cena mezi PDL a PDH.
- Asie: sweep Asie H (3889.6) a návrat zpět; Asie L zatím nesebrán, PDL nezasažen.
- Short na PDL, pokud se udrží pod NY open.

### NAS100
![[2026-11-17_0809_NAS100.png]]
- Denní: nižší vrcholy, cena u PDL 27234.75 (cíl trefen).
- Asie: odraz nahoru k Asie H, pak zpět dolů; struktura klesající.
- Short, ale pozor na sweep dolů a obrat.

### SPX500
![[2026-11-17_0809_SPX500.png]]
- Denní: silný pokles, cena těsně nad PDL.
- Asie: neúspěšný odraz k Asie H, zase dolů pod NY open.
- Short; Asie L 7414.75 zatím nesebrán, možný sweep a odraz.

### Průběžné vyhodnocení
Vyhodnocení: 20 zápisů za 3 obchodní dny (nových 10). Claude: n 13, směr 53.8 % (z +0.28), cíl 61.5 %. Pravidla: n 14, směr 42.9 % (z -0.53), cíl 57.1 %. Při neshodě s pravidly: n 4, směr 100 %. Pravidlo předem: rozhoduje se až po ≥ 30 dnech a ≥ 100 zápisech long/short; z čísel zatím nic nevyvozuji.

## New York (14:09)
Signály bota dnes: žádné (v logu dnes žádný SIGNAL, otevřený ani zavřený obchod).

| Trh | Můj bias | Bias pravidel | Cíl | Co hlídat |
|---|---|---|---|---|
| EURUSD | short | short | PDL 1.09938 (trefen), dál Asie L 1.09878 | cena se drží u PDL; short po MSS pod NY open 1.1007, long jen po zpětném zisku NY open |
| GBPUSD | neutral | short | PDL 1.31782 (trefen) | sweep Asie L proběhl, cena kolem NY open 1.3192; čekat na sweep Asie H 1.3203 nebo MSS |
| XAUUSD | short | short | PDL 3835.20 | po sweepu Asie H pokles pod NY open 3877.6; PDL ještě netrefen |
| NAS100 | long | short | NY open 27348 → Asie H 27498 | v Londýně sweep PDL/Asie L (~27150) a ostrý odraz; hlídat držení nad NY open a MSS |
| SPX500 | long | short | NY open 7434 → Asie H 7456.75 | sweep PDL/Asie L (~7405) a odraz nad PDL; hlídat držení nad 7420 |

### EURUSD
![[2026-11-17_1409_EURUSD.png]]
- Denní: silný pokles, cena na PDL, cíl pravidel splněn.
- 15m: sweep Asie L (~02:00), odraz k Asie H, návrat pod NY open; teď úzký pohyb u PDL.
- Struktura zůstává klesající, proto short (shoduji se s pravidly).

### GBPUSD
![[2026-11-17_1409_GBPUSD.png]]
- Denní: pokles z vrcholů, cena nad PDL.
- 15m: sweep Asie L a odraz, cena kolem NY open, pod Asie H.
- Neutral – nesouhlasím s pravidly (short): cíl i likvidita dole jsou už sebrány, chybí MSS.

### XAUUSD
![[2026-11-17_1409_XAUUSD.png]]
- Denní: dlouhý pokles, cena mezi PDL a PDH.
- 15m: sweep Asie H, návrat pod NY open; Asie L ani PDL nesebrány → likvidita dole zbývá.
- Short na PDL.

### NAS100
![[2026-11-17_1409_NAS100.png]]
- Denní: nižší vrcholy, ale dnešní sweep PDL s odrazem.
- 15m: v Londýně sweep PDL a Asie L, silný odraz nad NY open.
- Long – nesouhlasím s pravidly (short): cíl PDL i likvidita dole jsou sebrány a struktura se po sweepu otočila; riziko je silný denní trend dolů.

### SPX500
![[2026-11-17_1409_SPX500.png]]
- Denní: silný pokles, cena těsně nad PDL.
- 15m: sweep Asie L a PDL v Londýně, odraz nad NY open k 7440+.
- Long – nesouhlasím s pravidly (short), stejný důvod jako u NAS100; zneplatní to návrat pod PDL.
