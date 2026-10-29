---
tags: [fm, zdroj, strategie, swing]
zdroj: "D:\\youtube\\FM pdfka\\Strategie\\Daniel Hvězda - Swing Trading Strategie (PDF)"
zpracovano: 2026-10-29
---
# FM – Daniel Hvězda: Swing Trading (S/D W1 + D1, COT, sezónnost)

26 PDF, 182 stran. Obchoduje forex, indexy, zemědělské komodity, kovy a akcie. Pozice drží dny až měsíce.
Analýzu dělá na **futures grafech** (CME), obchoduje na CFD. JPY futures = obrácený USDJPY. Viz [[FM materiály]].

## Strategie (trading plán + entry model)
**„Denní level v týdenním levelu“:** S/D zóna na D1, která leží uvnitř S/D zóny na W1.

| Prvek | Pravidlo |
|---|---|
| Trend | Obchoduje jen ve směru trendu. Uptrend = **2 po sobě jdoucí vyšší maxima a 2 vyšší minima**, downtrend zrcadlově. V range víc fundamentu, čeká na potvrzení. |
| Zóna | Týdenní příjem: zóna W1, vstup na D1. Denní příjem: zóna D1, vstup na H4. |
| Lokace | **Fibo od low demand zóny k high supply zóny** (nejbližší zóny) rozdělí trh na třetiny: 0–33 % levné (long), 33–66 % equilibrium (čekat), 66–100 % drahé (short). → [[Premium a discount]] |
| Vstup | **Buy limit / sell limit** na zónu (proximal). Agresivnější vstup jen při silné reakci a potvrzení. |
| SL | Pod low demand, nad high supply. Občas **+20 % SL**: k SL se přidá 20 % jeho vzdálenosti. |
| TP | Nejbližší protilehlá S/D zóna nebo klíčová úroveň. RRR alespoň 1:2. |
| Správa | Při **1:1 SL na BE**. |
| Fundament | Extrémy **COT** (commercials, COT index), sezónnost (Seasonax). Red folder zprávy: NFP, FOMC, CPI, GDP, PMI… |
| Rating | **A+** = trend, D level krytý W levelem, fundament souhlasí, silná imbalance, RRR ≥ 1:2. **B** = chybí krytí W nebo trend, RRR ~1:2. Bez A+ je lepší čekat. |
| Risk | Funded 1 %, výzva 2 %. Po sérii ztrát snížit risk. |

## Jak kreslí S/D zónu → [[Supply a demand zóny]]
- **Zóna = pohyb dovnitř** (několik středně velkých nebo 2+ velké svíčky) **+ konsolidace** (menší nerozhodné svíčky)
  **+ pohyb ven** (několik středních nebo 2+ velké svíčky).
- Postup: od aktuální ceny se podívat doleva dolů (demand) nebo nahoru (supply), najít pohyb ven, pak pohyb dovnitř
  a mezi nimi konsolidační svíčky. Zóna se ohraničí dvěma vodorovnými čarami.
  Určí se **širší verze zóny a preferovaná verze** (užší).
- Na obrázcích je zóna **na výrazném swingu**, od extrému knotu po okraj těl báze.
  Demand je vždy pod cenou, supply nad ní.
- Typy podle FM: RKR (rally-base-rally), RKP, PKR, PKP.
- **Level nad levelem:** dvě S/D zóny těsně nad sebou (supply) nebo pod sebou (demand) zvyšují pravděpodobnost reakce.
- **S/R vs S/D:** S/R je čára, čím víc testů, tím je slabší. S/D je zóna z imbalance a obchoduje se návrat do ní.

## Svíčkové potvrzení v zóně → [[Svíčkové formace]]
- **Hammer:** malé tělo, spodní knot ≥ 2× tělo, malý nebo žádný horní knot. Vstup po další býčí svíčce, SL pod low.
- **Shooting star:** zrcadlově.
- **Engulfing:** tělo pohltí tělo předchozí svíčky. Vstup po close, SL za extrém formace, TP nejbližší protizóna.

## Patterny
- **Hlava a ramena:** vstup přes S/D, SL nad pravým ramenem, cíl = výška hlavy od neckline.
- **Cup with handle:** pokračování uptrendu.

## COT → [[COT]]
- **Commercials** (hedgeři) v extrému long → dno, v extrému short → vrchol. Funguje spolu s demand nebo supply zónou.
- **Fund managers / non-commercials** sledují trend; rekordní pozice znamenají vrchol nebo dno.
- **Retailers** jsou kontraindikátor.
- **COT index** 0–100 % (extrémy). Dále net position, open interest a spread commercials vs non-commercials.

## Testovatelnost
**Dobrá.** Všechno je na D1/W1, data máme (MT5 D1/W1 forex, zlato, indexy; COT zdarma od CFTC).
Návrh testu: zóny W1 a D1 podle pravidel výše, vstup limitem, SL za zónu (+ varianta 20 %), TP protizóna nebo 2R, BE při 1R.
Filtry trend (2 HH + 2 HL), lokace v třetinách a COT extrém. Srovnání s [[Náhodné vstupy|náhodnými vstupy]].

## Z grafů v PDF (prohlédnuto všech 117 obrázků, 2026-10-29)
- **Zóny jsou na výrazném swingu** (vrchol nebo dno, odkud přišel silný pohyb). Kreslí se od extrému knotu po okraj těl báze.
  Báze má 1–3 svíčky na W a 2–6 na D. Zóna je relativně vysoká, na W zhruba výška 1–2 svíček.
- **„Denní level v týdenním levelu“:** W zóna se zakreslí na W grafu a na D grafu pak D zóna, která se s ní **překrývá**
  (D zóna je uvnitř W zóny nebo ji protíná).
  **Vstup na proximal D zóny při prvním návratu, SL za distal W zóny** (pod celou spojenou zónu), TP velký,
  na obrázcích **RR ~3–5**, cíl na protější zóně nebo high.
- **Level nad levelem:**
  - Dvě zóny stejného směru nad sebou (v uptrendu dvě demand, „1st lvl“ blíž ceně a „2nd lvl“ pod ní).
  - Vstup na proximal 1. levelu, SL za jeho distal.
  - Když 1. level nevydrží, obchoduje se 2. level stejně. RR ~3–5.
- **S/D 2.0 diagramy (mechanika vstupu):**
  - Supply (růst → konsolidace → pád): **vstup na spodní hraně konsolidace, SL na horní hraně,
    TP = low, kam došel pád ze zóny** (extrém pohybu ven). Na diagramu RR ~1:2.
  - Demand zrcadlově: TP = high pohybu ven.
- **Trend** = šipky na swing high/low: uptrend = vyšší high i low, sideways = stejné úrovně. Vstupuje se na demand u nového HL.
- **COT na grafech:** svislé čáry v extrémech commercials (oranžová = extrém long, modrá = extrém short) se kryjí s dny a vrcholy
  týdenních grafů futures (6B, 6A, 6S). Indikátor je TradingView „COT“ (legacy).
- **Svíčky:** hammer a engulfing na dně nebo vrcholu po pohybu do zóny (fialové šipky).
