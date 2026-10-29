"""Doplni do vaultu materialy od uzivatele (dokument 6 strategii, exporty simulatoru, pozadavky) a presne
definice konceptu z dokumentu. Jen pridava/doplnuje - existujici poznamky neprepisuje (pripojuje sekce)."""
import os
import re

V = r"D:\Trading bot\znalosti"
DATE = "2026-10-29"


def write(path, tags, body):
    fp = os.path.join(V, path + ".md")
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, "w", encoding="utf-8").write(f"---\ntags: [{', '.join(tags)}]\naktualizovano: {DATE}\n---\n" + body.strip() + "\n")


def append(path, body, marker):
    fp = os.path.join(V, path + ".md")
    s = open(fp, encoding="utf-8").read()
    if marker in s:
        return
    open(fp, "w", encoding="utf-8").write(s.rstrip("\n") + "\n\n" + body.strip() + "\n")


# ------------------------------------------------------------------ materialy od uzivatele
write("Od uživatele/Dokument 6 strategií SMC + Volume Profile", ["od-uzivatele", "dokument"], """
# Dokument „Trading bot – 6 strategií (SMC + Volume Profile)“

Poslal uživatel 2026-10-28. Originál: ![[Trading bot – 6 strategií (SMC + Volume Profile).pdf]]
(též `.docx` v [[Přílohy]]; text i v `D:\\Trading bot\\scratch\\docx\\strategie.txt`).

## Obsah
- Předpoklady: kontext H4/H1, setup M15, vstup M1–M15 přes [[MSS a displacement|MSS s displacementem]]; časy v NY ([[Killzones a session]]).
- Trhy: EURUSD, GBPUSD, USDJPY, XAUUSD, XAGUSD, WTI, BTC, ETH, SOL; volume = tick volume z MT5.
- Stavební bloky: pivoty, struktura/BOS/MSS, displacement, RVOL, [[FVG]], [[Order block]], [[Supply a demand zóny]],
  [[Likvidita]], [[SFP – sweep likvidity|SFP]], [[Volume profile]], [[VWAP]], [[Daily Open a Power of 3|Daily Open]], [[Režim trhu]].
- 6 strategií: Sweep & Shift, zpřesněná S/D zóna, rotace ve Value Area, VWAP trend pullback, breakout z balance přes LVN,
  Daily Open manipulace (Power of 3).
- [[Risk management]]: 0,5 % na obchod, denní −2R, týdenní −5R, max 3 pozice, korelace, zprávy ±30 min.
- Postup testování: vizuální kontrola, bez look-ahead, M1 filly, 60/40 + [[Walk-forward]], [[Náhodné vstupy]], ablace, Monte Carlo.
  Prahy: n ≥ 100, expectancy ≥ 0,15 R, PF ≥ 1,3, DD95 ≤ 15 R, ziskové kvartály ≥ 60 %.

## Výsledek testu
Otestováno v [[F7 Dokument 6 strategií SMC]] → **nic neprošlo**. Věrná pravidla < 1 obchod/rok/trh (dokument odhadoval 1–5 týdně).
Kontrola detekcí: ![[f7_kontrola_detekci_BTCUSD.png]]

## Připomínka uživatele (2026-10-29)
S/D zóny podle dokumentu „hledá na špatných TF, moc malé“ → uživatel popíše, jak je kreslí sám (doplnit do [[Supply a demand zóny]]).
""")

write("Od uživatele/Export simulátoru 2026-10-28", ["od-uzivatele", "export"], """
# Export simulátoru za 1. den (2026-10-28)

`C:\\Users\\korda\\Desktop\\sft\\simulator-data-2026-10-28.json`. Účet 96 147 $ (start 100 000), 21 uzavřených obchodů,
78 [[Stínové obchody a verdikty|stínových]].
- Ztráty jen z 1m ukázek: `ukazka_ema_m1` 13 obchodů −1 491 $, `ukazka_m1` 8 obchodů −2 362 $ ([[Náklady brokera]] – spread ~70 % SL).
- [[AI analytik|AI]] správně odmítala 1m obchody.
- Opraveno podle rozboru: momentum v [[Učící režim|učícím režimu]] zkouší zablokované pozice znovu, AI do fronty místo přeskakování,
  pak vypnuty limity 2 % / 8 % v učícím režimu.
Další den: [[Export simulátoru 2026-10-29]].
""")

write("Od uživatele/Export simulátoru 2026-10-29", ["od-uzivatele", "export"], """
# Export simulátoru za 2. den (2026-10-29)

`D:\\Trading bot\\scratch\\exporty\\simulator-data-2026-10-29.json` (data od 2026-10-27 15:00 do 2026-10-29 08:45 UTC).

| | |
|---|---|
| Účet | **89 331 $** (−10,7 % od startu; den 1 byl 96 147 $) |
| Uzavřeno | 46 obchodů, −10 636 $ – **všechno 1m ukázky** |
| `ukazka_ema_m1` | 27 obchodů, −4 835 $, win 30 % |
| `ukazka_m1` | 19 obchodů, −5 801 $, win 5 % |
| Otevřeno | 26 pozic: 24× [[Momentum L=250]], 1× BB squeeze, 1× 1m ukázka |
| [[Průraz F2 (proraz_d1)|Průraz F2]], [[RSI(2) pullback (mr_rsi2_d1)|RSI(2)]] | za 2 dny žádný signál (normální – ~1 za 5 dní / jen po výprodeji) |

**[[AI analytik]]**: z 65 hlasů 64× NE; signály s NE skončily v průměru **−0,88 R** → AI měla pravdu.
Zamítnuté [[Stínové obchody a verdikty|stínové]] 1m obchody dopadly stejně špatně jako vzaté → problém je strategie, ne filtr.

**Závěr:** 1m ukázky jen pálí účet (potvrzuje [[Náklady brokera]] a [[F2 Více timeframů|F2]]). Doporučení: v Nastavení
vypnout `ukazka_m1` a `ukazka_ema_m1` (vypíná uživatel), ať [[Učící režim]] sbírá data jen ze smysluplných systémů.
Exporty jsou platné, i když výzkum F7 není commitnutý – simulátor běží z nasazeného kódu, F7 aplikaci neměnil.
""")

write("Od uživatele/Požadavky a nápady uživatele", ["od-uzivatele", "projekt"], """
# Požadavky a nápady uživatele (chronologicky)

- 2026-10-26: bot s agenty, vše zdarma, jen demo ([[Pravidla spolupráce]]).
- 2026-10-27: simulátor jako TradingView, agenti rozhodují o každém obchodu ([[Simulátor]], [[Agenti]]); bot 24/7 ([[Bot 24-7]]).
- 2026-10-27: „co největší win rate“, nemusí být 50 obchodů denně, ať fungují i AI boti ([[AI analytik]]).
- 2026-10-27: zprávy a skutečné hodnoty po vyhlášení ([[Zprávy a kalendář]]).
- 2026-10-27 večer: brát co nejvíc obchodů, ztráty nevadí, učit se z nich ([[Učící režim]]); i zamítnuté obchody zpětně vyhodnotit
  ([[Stínové obchody a verdikty]]).
- 2026-10-28: zkoušet jiné strategie než trend – S/R, fakeouty, SMC, S/D, OB, FVG, volume, FRVP, VAL/VAH, D open, likvidita
  ([[F5 SMC a volume profile na 1h]]).
- 2026-10-28: „30 % je málo“, hledat déle, cíl max win rate **nebo** asymetrie („1 obchod +10 000 a 3× −500 je OK“), risk management přes agenty
  ([[F6 Denní strategie]], [[Cíl projektu]]). Všechno ukládat na D.
- 2026-10-28: otázka na RR RSI(2) → ~1:0,65–0,8, profit z 71 % win ([[RSI(2) pullback (mr_rsi2_d1)]]).
- 2026-10-28: dokument 6 strategií – vše otestovat ([[Dokument 6 strategií SMC + Volume Profile]], [[F7 Dokument 6 strategií SMC]]).
- 2026-10-29: Obsidian jako „obrovská neuronka“ ([[00 Rozcestník]]).
- 2026-10-29: S/D zóny v dokumentu na špatných TF a moc malé – popíše sám ([[Supply a demand zóny]]).
- 2026-10-29: neuronka s popsanými prvky → AI je kombinuje a vymýšlí strategie ([[Databáze konceptů]]).
- 2026-10-29: vzít všechno z **FM** (PDF atd.) a udělat databázi trading konceptů podrobně popsanou ([[Databáze konceptů]]).
- 2026-10-29: MT5 neomezený počet svíček → test forexu a zlata na M1 ([[MT5 napojení]]).
- 2026-10-29: export za 2. den ([[Export simulátoru 2026-10-29]]); nainstalovat skill cloudflare/security-audit (hotovo).
""")

write("Od uživatele/Přílohy", ["od-uzivatele"], """
# Přílohy

Soubory ve složce `Přílohy`:
- ![[Trading bot – 6 strategií (SMC + Volume Profile).pdf]] – viz [[Dokument 6 strategií SMC + Volume Profile]]
- `Trading bot – 6 strategií (SMC + Volume Profile).docx`
- ![[f7_kontrola_detekci_BTCUSD.png]] – kontrola detekcí z [[F7 Dokument 6 strategií SMC]]

Sem patří i PDF z FM, až budou ([[Databáze konceptů]]).
""")

# ------------------------------------------------------------------ databaze konceptu
write("Koncepty/Databáze konceptů", ["koncept", "databaze"], """
# Databáze konceptů

Cíl (uživatel 2026-10-29): podrobně popsané trading koncepty z materiálů **FM** (PDF atd.) a z dokumentů,
aby z nich šlo skládat a testovat strategie. Každý koncept = jedna poznámka podle [[Šablona konceptu]].

## Stav
- Materiály FM: **zatím nedodány** (na PC nenalezeny) – doplnit do [[Přílohy]].
- Mechanické definice z [[Dokument 6 strategií SMC + Volume Profile|dokumentu 6 strategií]] jsou doplněné v konceptech níže.

## Koncepty
| Koncept | Skupina | Otestováno |
|---|---|---|
| [[SFP – sweep likvidity]] | SMC / likvidita | F5, F7 – bez výhody |
| [[Likvidita]] | SMC | F5, F7 |
| [[FVG]] | SMC | F5, F7 |
| [[MSS a displacement]] | SMC / struktura | F7 |
| [[Order block]] | SMC | F5 |
| [[Supply a demand zóny]] | SMC | F5, F7 – uživatel kreslí jinak (doplní) |
| [[Volume profile]] | objem | F5, F7 |
| [[VWAP]] | objem | F7 |
| [[Killzones a session]] | čas | F7 |
| [[Daily Open a Power of 3]] | čas | F5, F7 |
| [[Režim trhu]] | kontext | F7 |
| [[Mean reversion]] | styl | F1, F6 – funguje jen indexy |
| [[Trend following]] | styl | F2, F3, F6 |
| [[Turn-of-month]] · [[Carry]] · [[COT]] | jiné | F1, v1–v6 |

## Jak se z toho budou dělat strategie
Kombinace konceptů → [[Plán předem]] → test na datech ([[Výběr, kontrola, holdout]], [[Náhodné vstupy]]).
Pozor: čím víc kombinací, tím víc „vítězů“ náhodou – proto oddělené ověřovací období a korekce na počet testů.
""")

write("Koncepty/Šablona konceptu", ["koncept", "sablona"], """
# Šablona konceptu

Zkopíruj pro nový koncept do složky Koncepty a vyplň:

```
# Název konceptu
Zdroj: (FM / dokument / vlastní)  · Skupina: (SMC / objem / čas / styl)

## Definice
Co to je, jednou větou.

## Na jakém timeframu
Kontext / setup / vstup.

## Jak ho poznat (mechanicky)
- podmínka 1 (čísla! např. „tělo ≥ 1 ATR“)
- podmínka 2

## Obchod
- Vstup:
- SL:
- TP:
- Kdy neplatí / zrušení:

## Příklady
Screenshot dobrého a špatného příkladu.

## Souvisí s
[[...]]

## Otestováno
(doplní Claude – výzkum, výsledek)
```
Seznam všech konceptů: [[Databáze konceptů]].
""")

# ------------------------------------------------------------------ presne definice z dokumentu ke konceptum
DOC = "[[Dokument 6 strategií SMC + Volume Profile|dokumentu 6 strategií]]"
defs = {
    "Koncepty/SFP – sweep likvidity": """
## Definice z dokumentu
- Bearish SFP: high[i] překročí úroveň likvidity aspoň o 0,05 × ATR, ale close[i] je zpět pod úrovní (býčí zrcadlově).
- Varianta: návrat closem do 2 svíček.
- Průraz hlubší než 0,5 × ATR už není SFP, ale breakout – zahodit.
- Potvrzení objemem: RVOL svíčky ≥ 1,5 (spuštěné stop-lossy).
""",
    "Koncepty/Likvidita": """
## Definice z dokumentu
- BSL nad / SSL pod: PWH/PWL, PDH/PDL, high/low Asie a Londýna, EQH/EQL, poslední potvrzené swingy.
- EQH/EQL: aspoň 2 swingy v toleranci 0,1 × ATR a s rozestupem ≥ 5 svíček.
- Váha: PWH/PWL = 3, PDH/PDL a EQH/EQL = 2, session high/low = 1.
- Pool je vybraný, jakmile cena obchoduje za úrovní; vybraný přestává být cílem.
""",
    "Koncepty/FVG": """
## Definice z dokumentu
- Bullish FVG na svíčce i: low[i] > high[i−2], zóna [high[i−2], low[i]]; bearish high[i] < low[i−2].
- Minimum 0,25 × ATR, menší ignorovat. CE = střed mezery.
- Mitigace = první dotek; zneplatnění = close za vzdáleným okrajem; max stáří 100 svíček.
""",
    "Koncepty/MSS a displacement": """
## Definice z dokumentu
- Pivot: high[i] nejvyšší v okně i−N..i+N (N = 3 vstupní TF, N = 5 H1–D1); známý až po svíčce i+N.
- BOS: close (ne knot) za posledním potvrzeným swingem ve směru trendu.
- MSS: close tělem za swingem, ze kterého vyšel poslední pohyb do extrému (long = poslední swing high před nejnižším low).
  Swing blíž než 0,5 × ATR od extrému je moc malý → bere se předchozí.
- Displacement (1–5 svíček, končí closem za úrovní): průrazová svíčka tělo ≥ 1 ATR a ≥ 60 % rozsahu; celkem ≥ 2 ATR;
  efficiency ratio ≥ 0,6; max 1 opačná svíčka; průměrné RVOL > 1,0 (1–2 parametr); nechá FVG ≥ 0,25 ATR.
- Vstupní model: limit na CE FVG z MSS (varianty proximal hrana, open OB, market), SL za extrém + 0,1 ATR + spread,
  SL ≥ 5× spread.
""",
    "Koncepty/Order block": """
## Definice z dokumentu
- Bullish OB = poslední bearish svíčka (close < open) před displacementem, který udělal BOS/MSS a nechal FVG.
- Zóna [low, high] svíčky, varianta jen tělo [low, open]. Mean threshold = 50 %. Zneplatnění close pod low. Jen první dotek.
""",
    "Koncepty/Supply a demand zóny": """
## Definice z dokumentu
- Báze 1–4 svíčky, každá rozsah ≤ 0,7 × ATR a tělo ≤ 50 % rozsahu; odchod = displacement, cena se vzdálí ≥ 3× výšku báze.
- Demand: proximal = nejvyšší tělo báze, distal = nejnižší low báze vč. knotu odchodové svíčky (supply zrcadlově).
- Čerstvost: jen 1. dotek (varianta 2.); zóna zaniká closem za distal.
- Skóre 0–4: odchod ≥ 2 ATR, báze ≤ 2 svíčky, odchod udělal BOS, odchod nechal FVG.
- Zpřesnění: fixed-range profil přes bázi a první impulz, HVN uvnitř zóny ± 1 bin (bez HVN POC báze); LVN v zóně = cena proletí.

## Jak je kreslí uživatel
_(doplní uživatel – podle něj dokument hledá zóny na špatných TF a moc malé: TF, velikost, pravidla, screenshot)_
""",
    "Koncepty/Volume profile": """
## Definice z dokumentu
- Bin = denní ATR(14) / 40 (zaokrouhlený na tick); objem M1 svíčky rovnoměrně mezi biny od low po high.
- POC = bin s největším objemem; Value Area 70 %: od POC přidávat větší ze dvou sousedních dvojic binů.
- HVN/LVN: vyhlazení 5 biny; HVN = lokální max ≥ 50 % POC; LVN = lokální min ≤ 25 % POC mezi dvěma HVN.
- Profily: denní (pdPOC/pdVAH/pdVAL), kompozitní 20 dní, fixed-range. Naked POC (posledních 10 dní) jako magnet pro TP.
""",
    "Koncepty/VWAP": """
## Definice z dokumentu
- VWAP = Σ(p·v)/Σv, p = (H+L+C)/3, od začátku obchodního dne; σ = √(Σ v·(p−VWAP)²/Σv); pásma ±1σ, ±2σ.
- Anchored VWAP na významný swing/sweep.
- Sklon = (VWAP nyní − VWAP před 12 svíčkami M5) / ATR; |sklon| < 0,1 = plochý.
""",
    "Koncepty/Killzones a session": """
## Definice z dokumentu
| Událost | NY | Praha |
|---|---|---|
| Začátek dne forex/komodity | 17:00 | 23:00 předchozího dne |
| Začátek dne krypto (00:00 UTC) | 19:00/20:00 | 01:00/02:00 |
| Asie | 20:00–00:00 | 02:00–06:00 |
| London killzone | 02:00–05:00 | 08:00–11:00 |
| New York killzone | 07:00–10:00 | 13:00–16:00 |
| EIA (středa) | 10:30 | 16:30 |
MT5 ukládá svíčky v čase serveru – převést do NY (u tohoto brokera server = Londýn).
""",
    "Koncepty/Daily Open a Power of 3": """
## Definice z dokumentu
- DO = open první svíčky dne (forex/komodity 17:00 NY, krypto 00:00 UTC; varianta 00:00 NY). WO od neděle.
- Nad DO = premium, pod DO = discount; long hledat v discount, short v premium.
- Strategie: bias (D1 bullish, včera close nad POC, ne pod H4 supply, bez NFP/CPI/FOMC), Asie ≤ 0,4 denního ATR,
  v killzone sweep low Asie/PDL + SFP pod DO, MSS, CE pod DO; TP1 high Asie, TP2 PDH.
""",
    "Koncepty/Režim trhu": """
## Definice z dokumentu
- Balance: denní VA posledních 3 dní se překrývají ≥ 50 % a cena je uvnitř 20denní kompozitní VA.
- Trend: H4 struktura má BOS ve směru trendu za posledních 5 dní a cena je mimo kompozitní VA.
- Jinak neurčitý → trendové i range strategie vynechat.
""",
}
for path, body in defs.items():
    append(path, body + f"\nZdroj: {DOC}.", "## Definice z dokumentu")

# rozcestnik
append("00 Rozcestník", """
## Od uživatele
[[Požadavky a nápady uživatele]] · [[Dokument 6 strategií SMC + Volume Profile]] · [[Export simulátoru 2026-10-28]] ·
[[Export simulátoru 2026-10-29]] · [[Přílohy]] · [[Databáze konceptů]] · [[Šablona konceptu]]
""", "## Od uživatele")

# kontrola odkazu
names = set()
for root, _, files in os.walk(V):
    for f in files:
        names.add(os.path.splitext(f)[0] if f.endswith(".md") else f)
bad = []
for root, _, files in os.walk(V):
    for f in files:
        if f.endswith(".md"):
            s = open(os.path.join(root, f), encoding="utf-8").read()
            for m in re.findall(r"!?\[\[([^\]|#]+)", s):
                if m not in names:
                    bad.append((f, m))
print("neplatne odkazy:", bad or "zadne")
print("poznamek:", sum(1 for r, _, fs in os.walk(V) for f in fs if f.endswith(".md")))
