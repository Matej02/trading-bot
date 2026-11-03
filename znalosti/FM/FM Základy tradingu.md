---
tags: [fm, zdroj]
zdroj: "D:\\youtube\\FM pdfka\\Základy tradingu"
autor: Jan Šrajer (Funded Mind)
zpracovano: 2026-10-29
---
# FM – Základy tradingu (Jan Šrajer)

Základní kurz Funded Mind: 9 modulů + Basecamp a Launchpad, 111 PDF.
Shrnutí pravidel, která jdou převést do kódu. Koncepty jsou podrobně rozepsané v odkazovaných poznámkách.
Patří do [[FM materiály]].

## 1. Price Action → [[Market structure]], [[Support a rezistence]], [[Horizontální levely]], [[Trendline a kanály]]
- **Struktura:** uptrend = HH + HL, downtrend = LH + LL. Vyšší TF je vždy důležitější („banky se nerozhodují na M1“).
- **Externí struktura (swing)** se značí na W, D a H4 a dává trend a bias. **Interní struktura** (většinou M15) slouží ke vstupu a potvrzení.
  Vždy začínat externí.
- **BOS** = **close těla** za předchozím významným high/low (knot nestačí, to je jen test nebo sběr likvidity).
  **i-BOS** = to samé na interní struktuře. V uptrendu je i-BOS close pod posledním HL.
- **Strong vs weak high/low:**
  - Strong low = low, ze kterého růst prorazil předchozí high. Neočekává se jeho prolomení; když padne, mění se trend.
  - Weak high = high, po kterém pokles neprorazil předchozí low. Očekává se jeho prolomení a trend pokračuje.
  - Při značení se používá Fibonacci (úroveň je jen na obrázku, nezjištěno).
- **Nový swing** se značí až po „signifikantním pullbacku srovnatelném s předchozí price action“.
  Pomůcka: box kolem poslední struktury.
- **Kdy mechanické značení vynechat:** extrémně impulzivní pohyb bez korekcí, FOMC/NFP/CPI, nový trend na vyšším TF.
  Pak se řídit S/D zónami a HTF.
- **Line graf** (close) jako první pohled, když je svíčkový graf zašuměný.
- **Horizontální levely:**
  - Hierarchie M → W → D: měsíční jsou nejsilnější a nejméně přesné, denní nejpřesnější.
  - Značí se **podle těl**, ne knotů: dvě těla opačné barvy na stejné ceně. Měsíční jen z uzavřené svíčky.
  - Nejkvalitnější jsou **pivotní levely**.
  - Levely nejsou přímý vstup, jen bias a místa likvidity. Potvrzuje se reakcí na nižším TF.
- **Balanční level** = S/R flip: proražený support se stane rezistencí a naopak; vstupuje se na retestu.
- **Trendline:** od začátku trendu, co nejvíc dotyků těl bez prořezání.
  Změna trendu platí až po proražení trendline **i** struktury (posledního HL/LH).
- **Kanály:** rostoucí, klesající, range. V range jsou instituce v akumulaci a průrazy bez potvrzení bývají fakeouty.

## 2. Volume → [[Volume profile]], [[VWAP]], [[Futures data a objem]]
- **Forex nemá centrální objem.** Objem na TradingView je jen od jednoho brokera nebo tickový.
  Pravý objem dávají **futures CME**: 6E (EURUSD), 6B, 6J, 6A, 6C, 6S, 6N, DX (index dolaru), GC (zlato), ES/NQ (indexy).
- **S/D a levely se kreslí na unadjusted grafu** (adjusted posouvá ceny kvůli rolloveru).
- **Volume bars:** zelená čára = průměr objemu za 50 svíček.
  - Vysoký objem při růstu potvrzuje trend, nízký objem při průrazu znamená spíš fakeout.
  - Akumulace a distribuce = objem roste, cena stojí.
  - Extrémní objem a návrat do range = stop hunt.
- **Volume profile:**
  - HVN = magnet a S/R, LVN = cena projede. **Vstup na zóně uvnitř LVN je riskantní**, chce další potvrzení.
  - Value Area = 70 % objemu (VAH/VAL). POC nad cenou = rezistence, pod cenou = support.
  - **nPOC** (neotestovaný POC) = magnet.
  - **Acceptance vs rejection:** cena mimo VA se silným objemem znamená trend; slabý objem a návrat znamená fakeout.
- **Fixed range** (FRVP) přes konsolidaci nebo pohyb. Autorovi jde hlavně o **POC v kombinaci se S/D zónou** a Fibonacci.
- **Session profily:**
  - Časy v CEST: Asie 02–08 (range, profil tvaru D), Londýn 08–14:30 (průraz nebo fakeout Asie),
    NY 14:30–22 (pokračuje, nebo vrací „exces“ Londýna).
  - Nejdůležitější je **overlap Londýn → NY 14:30–17:00**.
  - Tvar profilu: D = balance, P/b = trend.
- **VWAP:**
  - Nad VWAP je trh býčí, pod ním medvědí.
  - Velký odstup od VWAP s klesajícím objemem = přetažený trh, čeká se pullback.
  - V balanci VWAP funguje jako magnet; v trendu instituce čekají na návrat k VWAP.

## 3. Risk management → [[Risk management]]
- **Golden rule:** nejvýš 1 % účtu na obchod (challenge 1–2 %, funded 0,5–1 %), RRR alespoň 1:2.
- **Denní limity:** max. denní ztráta −3 % (vlastní hranice −2 %), po 3 ztrátách v řadě konec dne.
- **Týden a recovery:** týdenní limit −6 až −8 %; při −5 % pauza a review, při −10 % zpátky na demo a backtest.
- SL se nikdy neposouvá proti sobě, jen na BE nebo do zisku.
- Slippage hrozí při zprávách (FOMC, CPI, NFP) a v nelikvidních časech (rollover ve 22 GMT, víkend). Čím menší SL, tím víc slippage bolí.

## 4. Supply & Demand → [[Supply a demand zóny]] (hlavní zdroj pro „jak kreslit zóny“)
- **Zóna = imbalance → balance (báze) → imbalance.** Formace RBR a DBR tvoří demand, DBD a RBD supply.
- **Pivotní zóny** vznikají na otočení trendu (swing high/low). Jsou to nejsilnější levely, „o 30–50 % silnější“.
  **Interní zóny** jsou uvnitř trendu (pullback): drží 1–2 dotyky, víc testů je oslabuje, reakce musí být rychlá a čistá.
- **Timeframy:**

  | Styl | Analýza | Vstup | Zóny |
  |---|---|---|---|
  | Day trading | 4H (struktura D1/W1) | M15 | 4H pivotní i interní, M15 jen upřesnění |
  | Swing | Týden | Den, 4H | jen pivotní D1/W1/M1, interní jen na správu pozice |
  | Poziční | Měsíc | Den, týden | |

- **Kreslení:**
  - Nástroj Parallel Channel s úrovněmi 0 / **0,75** / 1. Úroveň 0,75 má vlastní čáru, nejspíš pro vstup nebo zpřesnění (z textu nevyplývá).
  - Zóna obsahuje **celou konsolidaci**: na obrázcích D1 USDJPY má báze až 8–10 svíček, od extrému knotu po okraj těl.
  - Zóna, na kterou TF ještě neudělal impulzivní pohyb, se nekreslí; najde se na nižším TF (Weekly → Daily).
  - **Nejsilnější je zóna W a D, které se překrývají.**
  - RBR po velkém poklesu („příliš nízko“) je slabá: vznikla z přeprodanosti, ne ze zájmu.
- **Premium a discount** → [[Premium a discount]]: prodávat v premium (nad férovou cenou), kupovat v discount.
- **Postup day tradera:**
  1. 4H struktura: v bullish trendu hledat demand, v bearish supply.
  2. Zóna se zpřesní na M15.
  3. Konfluence: fixed range, high jako cíl.
  4. Vstup na dotek zóny, výstup na BE, když se cena vrací.
- **Ranní rutina:**
  - Zóny se kreslí na **M15 futures grafech (6E, 6J, 6B, 6A)** a přenášejí se na CFD.
  - Dotek zóny na futures platí, i když na CFD cena vypadá jinak.
  - Obchodují se jen ranní levely.
- **Swing:** nedělní příprava na M/W/D, přes týden 4H. Vstup jen z pivotní zóny, interní zóny slouží na pyramidování a BE.

## 5. Likvidita → [[Likvidita]]
- Velcí hráči vstupují **limitem** a potřebují protistranu (market ordery).
  Tu najdou ve stop lossech (95 % SL se vyplní jako market) a v buy/sell stopech při průrazech.
- **Tři typy poolů:**
  1. SL za major high/low a range extrémy.
  2. Stop ordery na průrazech (fakeouty).
  3. VWAP.
- Další místa likvidity: kulatá čísla, S/D zóny, HVN/LVN.
- **Sweep musí mít velký objem:**
  - **High-volume grab** = silný knot a rychlý návrat zpět. Typicky při otevření Londýna nebo NY a při zprávách; je to signál obratu.
  - **Low-volume grab** = průraz bez objemu, choppy návrat. Typicky v Asii, o svátcích a v noci; slabý signál.
- Neplést sweep likvidity s „failed auction“.

## 6.–9. Prop firmy, backtesting, journaling, futures
- **Prop firmy:**
  - One step: cíl +9 %, max DD 6 %, denní DD 3 %.
  - Two step: cíle 8 % a 5 %, max DD 9 %, denní 4 %.
  - Challenge projde 10–19 %.
  - Pravidlo „5 net wins“: při 1:2 a riziku 1 % stačí být o 5 obchodů v plusu.
- **Backtesting a journaling:** FxReplay a TradeZella. Test 2 strategií max, 1 setup, 20–30 obchodů, měřit winrate, průměrné RR a max DD.
  (Pro nás málo: viz [[Plán předem]] a [[Výběr, kontrola, holdout]].)
- **Futures:** tick a point value (ES 0,25 = $12,50, NQ 0,25 = $5, GC 0,10 = $10, 6E 0,00005 = $6,25), rollover zhruba týden před expirací, unadjusted graf.

## Basecamp a Launchpad
- Mentoři FM obchodují EURUSD, BTCUSD a XAUUSD, day trading 5–8 h denně. Cíl je prop firmy.
- **Swing strategie FM v kostce:** dlouhodobý trend → silný S/D level → konfluence (likvidita).
- **Day trading strategie FM v kostce:** vytvoření likvidity → **HTF order block s velkým objemem** → návrat do OB → entry model v HTF OB → **potvrzení RSI**.
- Strategie musí mít jasný trigger, invalidaci, TP plán, 1 setup, limit obchodů za den a max. denní ztrátu.

## Co z toho plyne pro bota
1. **S/D zóny hledat na D1/W1 (swing) nebo H4 (day)**, ne na M1–M15. M15 slouží jen k upřesnění.
   Báze = celá konsolidace mezi pohybem dovnitř a ven. Pivotní zóny (na swingu) jsou oddělené od interních.
   Přesně tohle F7 dělalo jinak ([[F7 Dokument 6 strategií SMC]]).
2. **Objem brát z futures nebo krypto burzy**, ne z tick volume brokera. U forexu je to v MT5 problém: viz [[Futures data a objem]].
3. Konfluence, které autor kombinuje: zóna + POC/nPOC + Fibo 50 % + trendline + session level. Zóna v LVN je slabá.

## Z grafů v PDF (prohlédnuto všech obrázků, 2026-10-29)
Obrázky z PDF (všechny grafy, po lekcích): [[FM obrázky – Základy – Likvidita]] (12) · [[FM obrázky – Základy – Price Action]] (32) · [[FM obrázky – Základy – Risk Management]] (22) · [[FM obrázky – Základy – Supply a Demand]] (136) · [[FM obrázky – Základy – Volume]] (49)

- **Šablony v TradingView:** Parallel Channel uložený jako šablony „Monthly / Weekly / Daily / 4H supply and demand“, „SCALP ZONE“ a „Channel 1“.
  Každý TF má vlastní barvu zóny, hierarchie je tedy M → W → D → 4H → scalp.
- **Validita zóny:** na grafu je u **prvního návratu** do zóny štítek „je validní“ (zelený) a u dalšího „není validní“ (červený).
  **Obchoduje se jen první návrat.**
- **Imbalance → balanc → imbalance:** svislé čáry oddělují impulz, konsolidaci (balanc) a další impulz. Zóna = balanc.
- **Báze na diagramech má 3–8 svíček** (rally/drop, pak malé až střední svíčky s knoty, pak velká svíčka ven).
  Flow diagram: „kupující převažují“ a pak „prodejci absorbováni“, což dává impulz.
- **Pivotní vs interní (diagram):** pivotní zóny (červené) jsou na každém swing high/low, interní (modré) uprostřed nohou trendu.
  Na grafu EURUSD: „OVERALL MS HIGH“ = pivotní supply, „INTERNÍ SUPPLY LEVEL“ a „VELMI SILNÁ IMBALANCE“ pod ní.
- **Typy patternů (praxe):**
  - **RBR:** báze 3–5 svíček (zelený box), popisek „silná zóna, jakmile cena dostane pullback zpátky do tohoto levelu“.
    Popisek „Rally-Base-Rally (RBR), typ continuation demand… pokud je RBR příliš nízko (po velkém poklesu), může být slabá“.
  - **RBD** na vrcholu: báze 3–4 svíčky a ostrý drop.
- **Day trading praxe (EURUSD):**
  - 4H demand (šedý box) po pullbacku, pak zpřesnění na M15 (červené pásy uvnitř).
  - **Long z M15 zóny, SL pod M15 zónou, TP zelený box RR ~3–4.**
  - Swing praxe: měsíční zóny (fialové), týdenní (žluté) a denní (modré) vnořené do sebe.
- **Day trading teorie:** v downtrendu swingové struktury jsou „pivotní 4H levely“ na swing high (supply) a swing low (demand).
  Interní zóny jsou mezi nimi.
- **Premium/discount:** Fibo 0 / 0,333 / 0,666 / 1 od MS low po MS high.
  Supply zóny v horní třetině (premium, červená) se obchodují short, demand ve spodní třetině long.
- **Likvidita s objemem (6E):**
  - „Nejedná se o výběr LQ“ = sweep highs s nízkým objemem.
  - „Jedná se o výběr LQ“ = sweep s velkým objemem, pak short s cílem **„na POC předchozí range“**.
  - „Málo volume značí Failed auction = bearish.“
  - Supply zóna slouží jako konfluence.
- **Fixed range:** popisky „předchozí range POC“, „key level“, **„kombinace demand levelu“** (POC uvnitř demand zóny) a „odraz z VAH“.
- **Volume bars:** šipky na velké objemové svíčky při průrazu z konsolidace (breakout) a na sweepy.
- **Seance:** Asie 02–08, Londýn 08–14:30, NY 14:30–22 (CET), overlapy mezi nimi. Session profily mají barvu podle seance a NY testuje VAH/VAL Londýna.

## Doplněno uživatelem (2026-11-03)
Viz [[Doplňující pravidla k FM PDF]], Část A (obecná pravidla uživatele napříč koncepty).
