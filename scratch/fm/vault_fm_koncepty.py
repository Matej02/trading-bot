"""FM část 1 → vault: nové koncepty (jen když neexistují) + sekce '## Z materiálů FM' do existujících (jen jednou)."""
import os

V = r"D:\Trading bot\znalosti"
HEAD = "---\ntags: [koncept, {tag}]\naktualizovano: 2026-10-29\n---\n"

NOVE = {
"Koncepty/Market structure.md": ("struktura", """# Market structure (BOS, i-BOS, strong/weak high/low)
Zdroj: FM (všichni autoři, hlavně [[FM Základy tradingu]]) · Skupina: SMC / struktura

## Definice
Uptrend tvoří HH + HL, downtrend LH + LL. Změna orderflow se projeví jako **BOS**, tedy close těla za významným swingem.

## Na jakém timeframu
- **Externí (swing) struktura** na W/D/H4 dává trend a bias. **Interní struktura** (M15, u Valcháře H1/M15) slouží ke vstupu.
- Vždy začít externí, protože vyšší TF má přednost.

## Jak ho poznat (mechanicky)
- **BOS** = close **těla** nad předchozím HH (uptrend) nebo pod LL. Knot je jen test nebo sběr likvidity.
  „Body tells the story, wicks do the damage“ (Kimmel).
- **i-BOS** = close těla za interním swingem; v uptrendu close pod posledním HL.
- **Strong low** = low, ze kterého růst prorazil předchozí high. Nemá padnout; když padne, mění se trend.
  **Weak high** = high, po kterém pokles neprorazil low; očekává se jeho průraz. Zrcadlově strong high a weak low.
- **Nový swing** se značí po pullbacku srovnatelném s předchozí price action (Šrajer používá Fibo, úroveň je jen v obrázku).
- **Trend podle Hvězdy:** 2 po sobě jdoucí vyšší maxima a 2 vyšší minima.
- **Změna trendu:** proražení trendline **i** posledního HL/LH (Šrajer). BOS + retest (Valchář).
  Downtrend se otáčí, když nevznikne nové low a cena prorazí minulé high (Hakimi).
- **CHoCH** = první, nejmenší změna struktury. Můčka ho jako spouštěč nedoporučuje.
- **Mechanické značení vynechat** po extrémně impulzivním pohybu, po FOMC/NFP/CPI nebo při novém trendu na HTF.

## Obchod
Struktura sama není vstup. Určuje směr (bias) a místa, kde hledat zóny ([[Supply a demand zóny]], [[Order block]]).
Vstupní spouštěč je MSS na LTF ([[MSS a displacement]]).

## Souvisí s
[[MSS a displacement]] · [[Trendline a kanály]] · [[Daily bias]] · [[Režim trhu]]

## Otestováno
Pivoty a BOS v [[F7 Dokument 6 strategií SMC]] jako součást setupů (samy netestovány).
"""),
"Koncepty/Support a rezistence.md": ("price-action", """# Support a rezistence (vč. balančních levelů)
Zdroj: FM ([[FM Základy tradingu]], Hvězda, Pátek, Veselovský, Můčka, Hakimi) · Skupina: price action

## Definice
Úroveň nebo spíš zóna, kde trh opakovaně reagoval: support je nákupní zájem, rezistence prodejní tlak.
Vyšší TF dává silnější levely.

## Jak ho poznat (mechanicky)
- Opakované reakce na stejné ceně. Kreslí se **podle těl** (dvě těla opačné barvy na stejné úrovni) → [[Horizontální levely]].
- **S/R vs S/D** (Hvězda): S/R je statická čára, čím víc testů, tím slabší (dobré v range).
  S/D je zóna z imbalance, obchoduje se návrat → [[Supply a demand zóny]].
- **Balanční level** (S/R flip):
  - Proražený support se stane rezistencí a naopak; vstup na retestu.
  - Veselovský a Hakimi: **knot proražený momentum svíčkou a pak opakovaně testovaný** (H1). Slouží jen jako konfluence.
  - Můčka: „protažený BOS“; entry, konfluence i target na všech TF.
- **Psychologické levely** = kulatá čísla.

## Obchod
- Jen jako kontext a konfluence. Samotný S/R není vstup (Šrajer, Veselovský).
- Pátek: SL za S/R a TP na další S/R; na LTF hodně fakeoutů, proto potvrzení.

## Souvisí s
[[Horizontální levely]] · [[Trendline a kanály]] · [[Likvidita]] · [[Market structure]]

## Otestováno
Zatím ne samostatně. Fakeouty S/R v [[F5 SMC a volume profile na 1h]] (SFP).
"""),
"Koncepty/Horizontální levely.md": ("price-action", """# Horizontální levely (M/W/D, opens)
Zdroj: FM ([[FM Základy tradingu]], Veselovský, Můčka) · Skupina: price action / čas

## Definice
Pevné cenové úrovně z vyšších TF a otevíracích cen, které trh respektuje.

## Jak ho poznat (mechanicky)
- **Hierarchie M → W → D:** měsíční jsou nejsilnější a nejméně přesné, denní nejpřesnější. Značí se od nejvyššího TF.
- **Podle těl, ne knotů.** Dvě těla opačné barvy na stejné ceně. Měsíční jen z uzavřené svíčky.
  Lokální levely se značí pravidelně (každou neděli).
- **Pivotní levely** jsou nejkvalitnější.
- **Opens** (Veselovský):
  - Daily open (DO), **NY daily open = 6:00 CET** (NY půlnoc) na H1, NY weekly open (pondělí 6:00) a monthly open.
  - Značí se od těla: u býčí svíčky spodek těla, u medvědí vršek.
  - **Cena nad DO/WO = bullish.** Průraz NY DO momentem na H1 bývá následovaný retestem a pokračováním.
- **Close předchozí svíčky** (D/W/M) jako pravděpodobnostní target (Můčka) → [[Daily bias]].

## Obchod
Bias a konfluence, ne samostatný vstup. Manipulace pro long má proběhnout pod NY DO → [[Daily Open a Power of 3]].

## Souvisí s
[[Support a rezistence]] · [[Daily Open a Power of 3]] · [[Daily bias]]

## Otestováno
D open a PO3 v [[F5 SMC a volume profile na 1h]] a [[F7 Dokument 6 strategií SMC]] (bez výhody). NY DO zatím ne.
"""),
"Koncepty/Trendline a kanály.md": ("price-action", """# Trendline a kanály
Zdroj: FM ([[FM Základy tradingu]], Pátek, Hakimi) · Skupina: price action

## Definice
Šikmá čára spojující swingy po směru trendu. Funguje jako dynamický support nebo rezistence.
Kanál = dvě rovnoběžky (rostoucí, klesající, boční).

## Jak ho poznat (mechanicky)
- Začít u začátku trendu a spojit co nejvíc **těl** bez prořezání (Šrajer). Alespoň 2 výrazné body (Hakimi).
- **Změna trendu = průraz trendline i struktury** (posledního HL/LH). Samotný průraz trendline nestačí.
- Průraz, retest z druhé strany a pokračování (Hakimi).
- **Breakout vs fakeout:** breakout má vyšší objem a silnou PA, fakeout slabý objem a rychlý návrat (Pátek).
- V range kanálu instituce akumulují a průrazy bez potvrzení bývají fakeouty.

## Obchod
- Pátek: trend v trendu (H4 → M30), vstup po průrazu pivotu na M5/M15 ve směru H4. SL za trendline.
- Hakimi: kanál jako součást konfluence s Fibo, S/D a Elliottem.

## Souvisí s
[[Market structure]] · [[Support a rezistence]] · [[Elliottovy vlny]]

## Otestováno
Ne (kreslení od ruky je těžko mechanizovatelné; náhrada = lineární regrese přes swingy).
"""),
"Koncepty/Premium a discount.md": ("smc", """# Premium a discount (lokace)
Zdroj: FM (Šrajer, Hvězda, Veselovský) · Skupina: SMC / kontext

## Definice
Poloha ceny v rozpětí mezi nejbližší demand a supply zónou (nebo swingem).
**Kupovat v discountu (levně), prodávat v premium (draze).**

## Jak ho poznat (mechanicky)
- **Šrajer (swing):** Fibo **0,333 / 0,5 / 0,666** mezi supply (od spodní hrany) a demand (od horní hrany) na HTF.
  **Top discount = long, top premium = short**, stačí 2R.
- **Hvězda (lokace):** Fibo od low demand zóny k high supply zóny.
  0–33 % velmi levné (long), 33–66 % equilibrium (čekat), 66–100 % velmi drahé (short).
- **Šrajer (day trading):** jedna ze 4 povinných podmínek entry modelu (M15 S/D v 4H S/D, likvidita, premium/discount).

## Obchod
Filtr lokace, ne spouštěč. Long jen ze spodní třetiny rozpětí, short z horní.

## Souvisí s
[[Supply a demand zóny]] · [[Fibonacci a golden pocket]] · [[Market structure]]

## Otestováno
Varianta „prem“ (filtr premium/discount) v [[F7 Dokument 6 strategií SMC]], S1 bez výhody. Na D1/W1 zónách zatím ne.
"""),
"Koncepty/Futures data a objem.md": ("objem", """# Futures data a objem (forex nemá centrální objem)
Zdroj: FM ([[FM Základy tradingu]], Hvězda, Šrajer, Kimmel) · Skupina: objem / data

## Definice
Forex je decentralizovaný. Objem v grafu je jen od jednoho brokera nebo **tickový** (počet změn ceny).
Skutečný objem mají futures na CME.

## Jak ho poznat (mechanicky)
- **Mapování:**
  - Forex: EURUSD → **6E**, GBPUSD → 6B, USDJPY → **6J (obráceně)**, AUDUSD → 6A, USDCAD → 6C (obráceně), USDCHF → 6S, NZDUSD → 6N, DXY → DX.
  - Komodity a indexy: zlato → **GC**, stříbro → SI, ropa → CL, S&P → **ES**/MES, Nasdaq → **NQ**/MNQ, Dow → YM.
- **Unadjusted graf** pro S/D a levely, protože adjusted posouvá ceny kvůli rolloveru.
  Rollover je zhruba týden před expirací (březen, červen, září, prosinec).
- FM mentoři **kreslí zóny na futures grafech a obchodují na CFD.** Dotek zóny na futures platí, i když na CFD cena vypadá jinak.

## Obchod
Volume profile, VWAP a sweepy „s velkým objemem“ mají smysl jen s reálným objemem.

## Souvisí s
[[Volume profile]] · [[VWAP]] · [[Zdroje dat]] · [[MT5 napojení]]

## Otestováno
V F5 a F7 jsme u forexu a zlata měli jen tick volume z MT5, u krypta reálný objem Binance. Volume koncepty nefungovaly ani na kryptu.
Zdarma futures M1 data nemáme (CME je placené, TradingView CME ~4 $/měs.), viz [[Zdroje dat]].
"""),
"Koncepty/Sezónnost.md": ("fundament", """# Sezónnost (seasonality)
Zdroj: FM (Hvězda, Valchář, Šrajer) · Skupina: fundament / čas

## Definice
Opakující se pohyby podle části roku: průměrný vývoj za 5, 10 nebo 15 let (Seasonax, Trading Analyzer).

## Jak ho poznat (mechanicky)
- Průměrný kumulativní výnos podle dne v roce za posledních N let (Trading Analyzer používá 10 let, skóre −2…+2).
- Příklady: **JPY posiluje v březnu** (repatriace před koncem japonského fiskálního roku), **CAD v zimě** (poptávka po ropě),
  EURUSD long v září (Šrajer).
- Prosinec a leden mají nižší likviditu (Hakimi).

## Obchod
Jen filtr pro swing: obchodovat ve směru sezónního trendu, nebo zkrátit držení proti němu. Nikdy samostatně.

## Souvisí s
[[COT]] · [[Makro skóre měn]] · [[Turn-of-month]]

## Otestováno
Zatím ne. Kandidát: měsíční sezónnost měn na D1 (pozor na data mining, 12 měsíců × 28 párů = hodně testů).
"""),
"Koncepty/DXY a dolar.md": ("fundament", """# DXY a dolar
Zdroj: FM (Valchář, Můčka, Hakimi, Šrajer) · Skupina: fundament / korelace

## Definice
Dolarový index (koš EUR 57,6 %, JPY, GBP, CAD, SEK, CHF). Podílí se na 80–90 % FX transakcí.

## Jak ho poznat (mechanicky)
- Trend a klíčové levely na DXY dávají bias pro USD páry. EURUSD je zhruba zrcadlo DXY.
- **Zlato a stříbro se pohybují obráceně k dolaru.** Korelace zlato–stříbro ~73 %.
- Vyšší sazby a inflace v USA posilují USD. Fundament je filtr před technikou.

## Obchod
Filtr: long EURUSD/XAUUSD jen při klesajícím DXY (pod jeho strukturou) a naopak. Korelace se rozpadá při vysoké volatilitě.

## Souvisí s
[[Makro skóre měn]] · [[COT]] · [[Zlato]] · [[Forex]]

## Otestováno
Ne. DXY je v MT5 jen u některých brokerů; jde ho spočítat z košíku párů.
"""),
"Koncepty/Makro skóre měn.md": ("fundament", """# Makro skóre měn (Trading Analyzer)
Zdroj: FM ([[FM Strategie – Jan Šrajer (day + swing)|Šrajer]], Valchář, Veselovský) · Skupina: fundament

## Definice
Každá z 8 měn dostane skóre ze sentimentu, ekonomiky a techniky. **Skóre páru = součet složek (−18…+18)**,
podle něj je bias. Nástroj je placený, metodika je v [[FM Strategie – Jan Šrajer (day + swing)|Šrajerových PDF]].

## Jak ho poznat (mechanicky)
| Složka | Rozsah | Složka | Rozsah |
|---|---|---|---|
| COT | −3…+3 | Úrokové sazby | −2…+2 |
| Retail sentiment (kontrariánsky) | −1…+1 | Manufacturing PMI | −2…+2 |
| GDP | −2…+2 | Services PMI | −2…+2 |
| CPI | −3…+3 | Retail sales | −2…+2 |
| Zaměstnanost | −4…+4 | Sezónnost | −2…+2 |
| | | Trend | −2…+2 |

- **Bias:** ≤ −9 velmi medvědí, −8…−5 medvědí, −4…+4 neutrální, +5…+8 býčí, ≥ +9 velmi býčí.
- **Signál = změna skóre o ≥ 2 body**, ne absolutní hodnota.
  Příklad: EURJPY −3 → 0 je býčí, i když cena padá; čeká se pullback a vstup ze zóny.
- Valchář: sleduje **momentum skóre**. Range a otáčející se skóre předznamenávají obrat;
  divergence cena–skóre dává protitrendový vstup ze silné S/D.

## Data
**Historie skóre je k dispozici:** 28 párů, denně 2017-01-01 (CAD páry od 2020-11-30) až 2024-10-03.
Leží v `research_data/fm_score/*.csv` (sloupce `timestamp, score`). Zdroj: FM, Šrajer swing, „3. Praxe data“.
Pozor: není jasné, zda je hodnota z rána nebo z večera. Při testu vstupovat až další den.

## Obchod
Pár se změnou skóre ≥ 2 → zóna ve směru změny → pullback → vstup, SL za zónu.

## Souvisí s
[[COT]] · [[Sezónnost]] · [[Carry]] · [[DXY a dolar]] · [[Zprávy a kalendář]]

## Otestováno
**Zatím ne. Silný kandidát:** reálná data skóre + D1 ceny z MT5 umožní ověřit „změna ≥ 2 → směr“ a „bias ±5 → trend“ proti náhodě.
"""),
"Koncepty/Daily bias.md": ("cas", """# Daily bias
Zdroj: FM (Veselovský, Můčka, Kimmel, Hakimi) · Skupina: čas / kontext

## Definice
Předpokládaný směr dne z denní svíčky a likvidity. Obchoduje se **jen ve směru biasu**, bias se během dne nemění.

## Jak ho poznat (mechanicky)
**Veselovský** (udává 70–80 % úspěšnost):
- Close těla **nad PDH** → dnes nahoru (pokračování).
- **Sweep PDH a close pod ním** → dnes dolů na PDL. Zrcadlově pro PDL.
- Close uvnitř knotu: nad 50 % knotu bullish, pod 50 % bearish.
- Range: neobchodovat, dokud se neuzavře mimo něj.
- K tomu D1 FVG a OB a vztah close k včerejšímu targetu.

**Můčka:** po **bearish denní svíčce cílit na PDL, po bullish na PDH** („velká pravděpodobnost“). Totéž s W a M svíčkami.
Další faktory: HTF, PA, session (Asie, Frankfurt) a **VWAP z předchozího dne**.

**Kimmel:** kde jsme a kam se dnes pravděpodobně pohneme (nejbližší interní nebo externí likvidita).

## Obchod
Filtr směru pro intraday modely ([[Daily Open a Power of 3]], [[MSS a displacement]]). Target dne = PDH/PDL.

## Souvisí s
[[Likvidita]] · [[Horizontální levely]] · [[Daily Open a Power of 3]] · [[SFP – sweep likvidity]]

## Otestováno
**Zatím ne. Rychlý a levný test na D1:** pro každý den spočítat pravidlo a pak zjistit, zda dosáhne cíle (PDH/PDL)
dřív než opačné strany. Srovnat s nepodmíněnou mírou (kolikrát se PDH/PDL trefí bez pravidla). Tisíce dní, víc trhů.
"""),
"Koncepty/Svíčkové formace.md": ("price-action", """# Svíčkové formace
Zdroj: FM (Hvězda, Pátek, Basecamp) · Skupina: price action

## Definice
Jedno- až třísvíčkové vzory obratu nebo pokračování. Mají smysl jen v kontextu (S/D zóna, S/R).

## Jak ho poznat (mechanicky)
- **Hammer:** malé tělo, spodní knot ≥ 2× tělo, malý nebo žádný horní knot. Objevuje se v demand nebo na konci downtrendu.
- **Shooting star:** zrcadlově (horní knot ≥ 2× tělo), v supply.
- **Engulfing:** tělo pohltí tělo předchozí svíčky. Čím větší, tím silnější.
- Doji, hanging man, morning/evening star, inverted hammer (Basecamp pojmy).

## Obchod (Hvězda)
- Hammer: vstup po potvrzovací býčí svíčce, SL pod low hammeru, TP nejbližší supply.
- Engulfing: vstup po close engulfingu, SL za extrém formace, TP nejbližší protizóna.

## Souvisí s
[[Supply a demand zóny]] · [[Support a rezistence]]

## Otestováno
Ne samostatně (v literatuře bez výhody; má smysl jen jako potvrzení v zóně).
"""),
"Koncepty/Elliottovy vlny.md": ("price-action", """# Elliottovy vlny
Zdroj: FM (Hakimi) · Skupina: price action / cykly

## Definice
Trend tvoří 5 impulzních vln (1–5), korekce 3 vlny (A-B-C). Popisují psychologii davu.

## Jak ho poznat (mechanicky)
- Vlna 2 nikdy nepřekročí začátek vlny 1.
- Vlna 3 je nejdelší z impulzních vln 1, 3 a 5.
- Vlna 4 nezasáhne do oblasti vlny 1.
- Impulzní vlny mají 5 subvln, korekční 3.

## Obchod
- SL za vlnu 2 nebo 4, TP podle očekávané vlny 3 nebo 5.
- Hakimi kombinuje s Fibo, kanálem, likviditou a S/D a kreslí víc scénářů najednou.

## Souvisí s
[[Fibonacci a golden pocket]] · [[Trendline a kanály]] · [[Market structure]]

## Otestováno
Ne. **Subjektivní**: „různí analytici mají různé vlny“. Mechanizace je sporná.
"""),
"Koncepty/Fibonacci a golden pocket.md": ("price-action", """# Fibonacci a golden pocket
Zdroj: FM (Šrajer, Veselovský, Můčka, Hakimi, Hvězda) · Skupina: price action

## Definice
Retracement impulzní vlny v poměrech Fibonacciho řady, natahuje se vždy zleva doprava.
**Golden pocket = 0,618–0,66.**

## Jak ho poznat (mechanicky)
- **Úrovně:** 23,6 / 38,2 / 50 / 61,8 / 66 / 70,5 / 75 / 78,6 / 88,6 %.
- **Šrajer:** první je 0,382; když padne, cena míří ke golden pocket. Swing chce hlubší retracement.
- **Veselovský:** 0,382 a 0,618–0,66 jsou optimální pullback na EURUSD; **0,705–0,75** dobře funguje na XAU a NQ.
  Vstup do první FVG s 0,382.
- **Můčka:** 61,8 % je nejsilnější. SL lze dát na 33 %, negativní Fibo slouží jako swing targety, Fibo ve velké zóně zpřesní level.
- **Lokace** (Fibo mezi zónami do třetin) → [[Premium a discount]].

## Obchod
Zóna vstupu po MSS: průnik golden pocketu s FVG, OB nebo S/D.

## Souvisí s
[[Premium a discount]] · [[FVG]] · [[MSS a displacement]] · [[Elliottovy vlny]]

## Otestováno
Vstup na Fibo ve variantách F7 (OTE 0,62–0,79 v S1/S5) bez výhody.
"""),
}

DOPLNKY = {
"Koncepty/Supply a demand zóny.md": """
## Z materiálů FM (část 1, 2026-10-29) – jak kreslí S/D zóny mentoři
Podrobně v [[FM Základy tradingu]], [[FM Strategie – Daniel Hvězda (swing)]] a [[FM Strategie – Jan Šrajer (day + swing)]].
**Liší se od dokumentu 6 strategií hlavně timeframem a velikostí zóny.** To nejspíš odpovídá výtce uživatele („špatné TF, moc malé“).
- **Skladba:** pohyb dovnitř (několik středních nebo 2+ velké svíčky) + **konsolidace** (menší nerozhodné svíčky) + pohyb ven.
  **Zóna obsahuje celou konsolidaci**: na obrázcích má báze na D1 až 8–10 svíček, od extrému knotu po okraj těl.
  Kreslí se dvěma vodorovnými čarami, s širší a preferovanou (užší) verzí. Nástroj Parallel Channel má úrovně 0 / 0,75 / 1.
- **Platnost** (Šrajer, Hakimi, Můčka):
  - Po zóně **musí přijít impulzivní svíčka, která „něco dokázala“: prolomila high/low (BOS)**.
  - Zóna je **unmitigated**: mitigace max. **25 %** zóny.
  - Interní zóna drží 1–2 dotyky.
- **Pivotní vs interní:**
  - **Pivotní** = na otočení trendu (swing high/low), „o 30–50 % silnější“. Jen z nich se otevírají swingové obchody.
  - **Interní** = uvnitř trendu (pullback), slouží na správu pozice, BE a pyramidování.
  - RBR po velkém poklesu je slabá (přeprodanost).
- **Timeframy:**
  - Swing: zóny **W1 a D1 (M1)**, vstup na D1/H4. Hvězda: **D zóna uvnitř W zóny**.
  - Day trading: **4H zóny** (pivotní i interní) zpřesněné na **M15**. Šrajer: M15 zóna uvnitř 4H zóny.
  - Zónu, na kterou daný TF ještě neudělal impulzivní pohyb, hledat na nižším TF.
- **Lokace:** demand jen v discountu (spodní třetina mezi zónami), supply v premium → [[Premium a discount]].
  Trend na HTF: v uptrendu jen demand.
- **Vstup:** limit na proximal. **SL za distal** (Hvězda občas +20 % vzdálenosti; Můčka nikdy přímo nad zónu). TP nejbližší protizóna, ≥ 2R.
  BE při 1R (Hvězda), nebo bez BE (Valchář, Hakimi).
- **Konfluence:** POC/HVN z fixed range uvnitř zóny ji potvrzuje; **zóna v LVN je slabá**. Svíčka (hammer/engulfing) v zóně.
  Level nad levelem (dvě zóny těsně u sebe).
- **Data:** zóny se kreslí na **futures unadjusted** grafech → [[Futures data a objem]].
""",
"Koncepty/Likvidita.md": """
## Z materiálů FM (část 1)
- **Proč existuje:** velcí hráči vstupují limitem a potřebují market protistranu.
  Tu najdou v SL (95 % SL se plní jako market), v buy/sell stopech na průrazech a u VWAP ([[FM Základy tradingu]]).
- **ERL vs IRL** (Veselovský, Kimmel): externí = swing H/L, PDH/PDL, lokální H/L, Asie; interní = FVG, BPR, iFVG.
  **Trh chodí z IRL do ERL a zpět.** Interní target je „méně bolesti hlavy“ (Kimmel).
- **Sweep s objemem:**
  - **High-volume grab** = silný knot a rychlý návrat; při otevření LO/NY a při zprávách je to signál obratu.
  - **Low-volume grab** (Asie, svátky, noc) = choppy návrat, slabý signál.
- **Bez výběru likvidity nevstupovat** (Veselovský, Můčka, Valchář: „vstupuji až po vybrání likvidity“).
- **Equal highs a pivotní likvidita** jako spouštěč do zóny: [[FM Strategie – Jan Šrajer (day + swing)|Šrajerovy entry modely 1–3]].
- Session H/L (Londýn, Asie) = zásobník stop lossů → [[Killzones a session]].
""",
"Koncepty/FVG.md": """
## Z materiálů FM (část 1)
- **FVG** = mezera mezi svíčkou 1 a 3 kolem impulzivní svíčky 2. **Reakce na 50 %** (Můčka, Hakimi).
  **Close za FVG ho ruší** (Veselovský). FVG ve směru trendu, jinak magnet a target.
- **iFVG:** FVG proražený closem, otočí směr a slouží jako zóna v novém směru.
- **BPR:** býčí a medvědí FVG se překrývají; BPR je část, do které nezasahují knoty.
- **Gap vs FVG:** gap se musí zaplnit celý a je to target, ne vstup.
- Vstup po MSS do **první FVG s 0,382** (Veselovský), na M5 přednostně FVG (Můčka).
""",
"Koncepty/Order block.md": """
## Z materiálů FM (část 1)
- **Poslední opačná svíčka před impulzem.** **Musí způsobit BOS** (Valchář) a **vzniknout na důležité úrovni**
  (po sweepu likvidity, ve FVG; Veselovský). Jinde se mu nepřikládá váha.
- Jedna svíčka se bere celá i s knotem, skupina svíček jen těly. **Vstup na 50 % OB** zlepší RR (Veselovský).
- Spolehlivější na 1H/4H/1D. Potvrzení vstupu MSS na M1/M5. SL za OB, TP nejbližší likvidita, ≥ 1:2.
- **OB vs S/D** (Můčka): OB je poslední opačná svíčka, S/D je místo akumulace. Nejlepší je kombinace obou.
- **FM day trading v kostce** (Launchpad): vytvoření likvidity → **HTF OB s velkým objemem** → návrat → entry model v OB → potvrzení RSI.
""",
"Koncepty/MSS a displacement.md": """
## Z materiálů FM (část 1)
- **Veselovský:** MSS na **M1/M5** po sweepu likvidity: trh prorazí low/high, které tvořilo BOS.
  **Musí mít displacement (momentum)** a **vzniknout v důležité zóně** (OB/FVG/iFVG/BPR), jinak je bezcenný. Knot nestačí.
  Pak limit do první FVG s 0,382 nebo golden pocket. SL ±2 pipy za swing.
- **Můčka:** structure shift na M1 (A+ zóny) nebo M5 (A/B). Může to být i průraz nejbližší S/D zóny. **CHoCH nedoporučuje.**
  SL 8–12 pipů EURUSD, nikdy < 6, přímo na high/low.
- **Kimmel:** rozhodují close svíček. Model 2 vyžaduje **2 po sobě jdoucí změny struktury ve směru biasu**.
""",
"Koncepty/Volume profile.md": """
## Z materiálů FM (část 1)
- **HVN** = magnet a S/R. **LVN** = cena projede; **vstup na zóně uvnitř LVN je riskantní** a chce další potvrzení.
- **Value Area 70 %:** uvnitř rotace kolem POC. Acceptance mimo VA se silným objemem znamená trend; rejection se slabým objemem návrat.
- **nPOC** (neotestovaný POC předchozí seance) = magnet a target (Šrajer, Můčka, Hakimi). V TradingView zapnout „Extend POC right“.
- **Tvary:** D = balance, P = short covering, b = long liquidation, thin = rychlé průrazy.
- **Session profily:** Asie má profil D (mean reversion), Londýn průraz nebo fakeout Asie, NY testuje POC/VAH/VAL Londýna.
- **Fixed range** přes trend nebo korekci (Valchář): POC/HVN, který se kryje se S/D zónou, je potvrzení.
- U forexu je profil jen z tick volume → [[Futures data a objem]].
""",
"Koncepty/VWAP.md": """
## Z materiálů FM (část 1)
- Nad VWAP je trh býčí, pod ním medvědí. V balanci je VWAP magnet. **Velký odstup s klesajícím objemem** = přetažený trh, čeká se pullback.
- **Close VWAP předchozího dne** = bias a pravděpodobnostní target (Můčka).
- VWAP je jeden ze 3 typů poolu likvidity (instituce a algoritmy obchodují kolem něj).
""",
"Koncepty/Killzones a session.md": """
## Z materiálů FM (část 1) – časy v CET/CEST
| Autor | Okna |
|---|---|
| Šrajer DT | 8:30–9:30, 10:30–11:30, 13:30–16:00; Asie ne |
| Veselovský | Londýn 8–11 (long i 11:30), NY 14–17 (bez zpráv od 13:00); Asie 2–8 = akumulace |
| Můčka | obchoduje 9–11 a 13:30–17; boxy Asie 2–6, Frankfurt 8–9, Londýn 9–17, NY 14–22 |
| Valchář | Londýn impulz 9–12 (box 9–11:30, H/L do 17), NY overlap 14:30–17 (box 15:30–17:30) |
| Kimmel (indexy) | 15:30–19 (entry model 1 jen 15:30–18) |
| Základy | Asie 2–8, Londýn 8–14:30, NY 14:30–22; nejdůležitější overlap 14:30–17 |
- **Londýn často sweepne Asii a pak jde trendem** (Valchář). **NY často retestuje London H/L.**
- Můčka: sweep Asia H/L v Londýně platí jen při **asijském range ≤ 35 pipů** (EURUSD).
""",
"Koncepty/Daily Open a Power of 3.md": """
## Z materiálů FM (část 1)
**AMD (Veselovský):**
1. **Akumulace** v Asii.
2. **Manipulace** = sweep likvidity proti směru; **pro long pod NY daily open (6:00 CET), pro short nad ním**.
3. **Distribuce** = hlavní pohyb dne k opačné likviditě.

Vstup po MSS s displacementem. TP1 je opačná strana Asie (pak BE), TP2 daily bias target (PDH/PDL). → [[Daily bias]]
""",
"Koncepty/COT.md": """
## Z materiálů FM (část 1)
- **Commercials (hedgeři):** extrém long znamená dno, extrém short vrchol, hlavně spolu se S/D zónou (Hvězda; příklady GBP, AUD).
- **Non-commercials / leveraged funds:** sledují trend; rekordní pozice signalizují blížící se obrat.
  Změna v čase a **divergence cena–COT** (Valchář, Šrajer).
- **Retail / non-reportables:** kontraindikátor.
- **COT index 0–100 %:** extrémy. Rostoucí open interest s net pozicemi posiluje trend (Můčka).
- V [[Makro skóre měn]] má COT váhu −3…+3.
""",
"Koncepty/SFP – sweep likvidity.md": """
## Z materiálů FM (část 1)
- **Šrajer:** sweep pivot equal highs nebo pivot liquidity **do M15 zóny uvnitř 4H zóny**. Nebo sweep → lokální MSS → retest local demand (RR ~3).
- **Kimmel:** dotyk PDH/PDL nebo oblasti předchozího dne na M15, reverzní signál na M5/M1 v 15:30–18:00, **SL 25 % za extrém**.
- **Můčka:** sweep Asia H/L v Londýně jen při Asii ≤ 35 pipů.
- **Objem:** sweep má mít velký objem (stažená svíčka), jinak je to slabý low-volume grab ([[Likvidita]]).
""",
"Koncepty/Režim trhu.md": """
## Z materiálů FM (část 1)
- Range znamená, že retail ztrácí na fakeoutech. **Veselovský neobchoduje, dokud se trh neuzavře mimo range.**
- Hvězda: v trendu technika, v range víc fundament a čekání na potvrzení. Valchář: nesoulad weekly a daily biasu = žádný vstup.
""",
"Metodika/Risk management.md": """
## Z materiálů FM (část 1)
- **Na obchod:** 1 % (challenge 1–2,5 %, funded 0,5–1 %). Valchář podle ratingu A+ 1,25 / A 1 / B 0,75 %.
  Kimmel na futures funded 10–20 % dostupného drawdownu.
- **Limity:** max. denní ztráta −3 % (vlastní −2 %), Veselovský max. 2 SL za den po 0,5 %, **po 3 ztrátách v řadě konec dne**.
  Týden −6 až −8 %; při −5 % pauza, při −10 % zpět na demo.
- **RRR:** min. 1:2 (Hakimi 2,5, Šrajer průměr 2,7). **Názory na BE se rozcházejí:**
  Hvězda BE při 1R a Veselovský BE po TP1; Valchář, Pátek a Hakimi BE nepoužívají („ničí statistiku“).
- Zdroj: [[FM Základy tradingu]] a jednotlivé strategie ve [[FM materiály]].
""",
"Infrastruktura/Zprávy a kalendář.md": """
## Z materiálů FM (část 1)
- **Průměrný pohyb EURUSD za prvních 15 min** (Můčka): CPI 59,8 pipu, FED 59,9, NFP 56,8, ECB 34,7, PMI 26–27, retail sales 25, GDP 25,
  PPI 20, nezaměstnanost 20, PCE 17.
- **Kdo co neobchoduje:**
  - Veselovský: FOMC, NFP, PPI, CPI, PMI.
  - Hakimi (zlato): NFP, FOMC, Core PPI.
  - Valchář: nevstupuje 2 h před red news, a když je cena blízko vstupu, zavírá.
- Pohyb proti výsledku zprávy je manipulace; pak se hledá vstup ve směru fundamentu (Veselovský, Hakimi).
  Můčka odhaduje směr z pohybu před zprávou („7 z 10“).
""",
"Trhy/Zlato.md": """
## Z materiálů FM (část 1)
- FM mentoři obchodují XAUUSD hlavně intraday ([[FM Strategie – Sunita Hakimi (day, zlato)|Hakimi]], Můčka, Šrajer). Futures symbol GC.
- **Frankfurt session (8–9 CET) na zlatě** je pravděpodobnostní level pro vstup (Můčka).
- Zlato jde obráceně k DXY a roste s inflací a při nízkých sazbách. Korelace se stříbrem ~73 %.
- Fibo 0,705–0,75 „dobře reaguje na XAU“ (Veselovský).
""",
}


def main():
    made, appended, skipped = [], [], []
    for rel, (tag, body) in NOVE.items():
        p = os.path.join(V, rel)
        if os.path.exists(p):
            skipped.append(rel)
            continue
        with open(p, "w", encoding="utf-8") as f:
            f.write(HEAD.format(tag=tag) + body)
        made.append(rel)
    for rel, add in DOPLNKY.items():
        p = os.path.join(V, rel)
        if not os.path.exists(p):
            skipped.append(rel + " (neexistuje)")
            continue
        txt = open(p, encoding="utf-8").read()
        if "## Z materiálů FM" in txt:
            skipped.append(rel + " (už má FM)")
            continue
        with open(p, "a", encoding="utf-8") as f:
            f.write(("" if txt.endswith("\n") else "\n") + add)
        appended.append(rel)
    print("nové:", len(made), made)
    print("doplněné:", len(appended))
    print("přeskočené:", skipped)


main()
