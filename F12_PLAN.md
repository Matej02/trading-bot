# F12 – Můčka podle doplňujících pravidel uživatele (plán předem, 2026-11-03)

Zdroj pravidel: `znalosti/Od uživatele/Doplňující pravidla k FM PDF.md` (A = obecná, B1 = Petr),
celý text Petrových PDF (`scratch/fm/mucka_vse.txt`) a všech 196 obrázků (`znalosti/FM/Obrázky/FM obrázky – Petr Můčka (day).md`).
Odkazy: [A2] = dokument uživatele, [obr N] = číslo obrázku v galerii, [PDF lekce] = Petrův text.

## 1. Struktura (stejný kód pro 4H a 15m) [A2, B1, obr 69–72, 112–115]
- Swing = ZigZag na **zavíracích cenách**, min. otočka k × ATR(14) daného TF [A2 „pro kód“]. k je volný parametr
  (uživatelovy screenshoty 6E 15m nemáme) → varianty k ∈ {1,5; 2,5; 4} vybírané jen na vývoji + obrázky ke kontrole uživatelem.
  Úroveň swingu = extrém (knot) svíček u pivotu, varianta: zavírací cena (line chart).
- **BOS** = svíčka uzavře **tělem** za weak levelem [A2]:
  - nestačí „lehce“: close ≥ 0,1 ATR za úrovní a další svíčka nezavře zpět [A2];
  - momentum: tělo ≥ průměr těl (20) a svíčka po ní stejné barvy, nebo objem nad MA50 [A2, A7, PDF MS teorie];
  - ne extrémní news svíčka: tělo ≤ 3 ATR [A2].
- **Strong level** = extrém mezi swingem, ze kterého je BOS, a svíčkou průrazu; posouvá se s každým BOS [A2, obr 69–72, 112–115].
- **Weak level** = extrém po průrazu, „zakreslí se“ až po pullbacku ≥ 0,382 (tolerance 0,35) Fibo od strong k extrému.
  Bez pullbacku se extrém dál posouvá [A2].
- Close za strong levelem = změna trendu (nový BOS opačným směrem od strong levelu).
- Platnost BOS: stáří 4H 30 dní, 15m 5 dní; po prvním návratu ceny na úroveň BOS je mitigovaný [A2].
  **První návrat = balanční level jako místo vstupu** [PDF Balanční levely, obr 1–6].
- Interní struktura: stejný stroj s menším k (I-BOS). Váhy se zatím neřeší [B1].

## 2. Směr (top-down) [obr 76–77, PDF Trend, B1]
- D1: bias podle close včerejší svíčky (bullish → cíl PDH, bearish → PDL) [PDF Daily bias, obr 7–15], varianta i trend D1.
- 4H hlavní struktura ve stejném směru (platný BOS) → 15m pullback → vstup na 5m/1m ve směru D1 a 4H.

## 3. Zóny pro vstup (POI), připravené na 4H a 15m [PDF Entry model „bez kvalitních zón nefunguje“]
- S/D zóna, **která způsobila BOS** [PDF S/D, obr 93–96 ✓/✗]:
  - hranice přes těla [A4]; base 1–5 svíček, odchod s momentem;
  - platí jen první dotek a neplatí po proniknutí > 25 % hloubky (close) [A4];
  - varianta: zóna obsahuje POC/HVN objemu (M1 tick volume přes base + odchod) [A4, A7].
- Balanční level: první návrat na úroveň platného BOS (4H nebo 15m) [PDF Balanční levely].
- Varianta POI: jen zóny / jen balanční levely / obojí.

## 4. Entry model na 5m nebo 1m [PDF Entry model, obr 160–175, B1]
1. Cena v POI během killzone **9:00–11:00 a 13:30–17:00 místního času** (Praha, UTC+1/+2) [PDF Killzones, A1].
2. Vybere likviditu: low (long) nižšího TF pod posledním swingem, uvnitř POI [obr 160, PDF Likvidita „vždy vybraná LIQ“].
3. **MSS**: close tělem s momentem nad posledním lower high (swing ZigZag na 5m/1m). CHoCH se nepoužívá [B1].
4. Limit **lehce před zónou** (+spread): 0,618–0,66 nohy od sweepu k maximu po MSS [obr 160], na 5m varianta 50 % FVG z MSS nohy [obr 174–175, PDF FVG].
   Platnost limitu do konce killzone.
5. **SL přímo na low sweepu** bez rezervy; min. 6 pipů EURUSD (rezerva jen tehdy); nad ~15 pipů obchod vynechat (8–12 je jeho norma).
   Jinde přepočet přes ATR D1 jako v F11 [PDF Entry model SL].
6. **TP** na jedné úrovni (bez TP1/TP2 a bez BE) [PDF RRR, Úvod do RM], RR ≥ 2. Varianty:
   - (a) nejbližší pravděpodobnostní level s RR ≥ 2: Asia H/L, PDH/PDL podle biasu, close VWAP včerejška, nPOC včerejška [obr 178, PDF Statistiky];
   - (b) pevně 2,5 R (jeho průměr) [PDF RRR].
   Strop 5 R. Zavřít do konce dne (22:00), přes noc nedrží [PDF Úvod].
7. Bez vstupů v den red news USD/EUR 30 min před zprávou [A8, PDF Novinky] (podle dat z F10).

## 5. Data a vyhodnocení
- Trhy: EURUSD (hlavní), XAUUSD, NAS100mini (jeho trhy), GBPUSD, XAGUSD (podle PDF jde i na ně). MT5 M1, s náklady brokera.
- Vývoj do 2021 (indexy od 2019-02), **OOS 2022–2026**. Varianta (k, POI, TF vstupu, typ vstupu, TP) se vybírá jen na vývoji.
  Mřížka nejvýš 3 × 3 × 2 × 2 × 2 = 72.
- Náhodné vstupy: stejné časy, směr a vzdálenosti SL/TP, ale náhodný den. Kontrola zpožděného vstupu (look-ahead).
  Výsledek bez nákladů.
- Prahy jako dřív: n ≥ 100, exp ≥ 0,15 R, PF ≥ 1,3 a aspoň o 0,1 R nad náhodou.
- **Obrázky:** struktura 4H a 15m EURUSD (BOS, strong/weak, zóny) a ukázky obchodů. Uživatel je porovná se svým kreslením.

## Předpoklady (z materiálu nejdou přesně zjistit)
- velikost otočky ZigZag (k);
- „velmi blízko 0,382“ = 0,35;
- „lehce za úrovní“ = < 0,1 ATR;
- „extrémní news svíčka“ = tělo > 3 ATR;
- 25 % zóny měřeno zavřením 15m svíčky;
- max SL 15 pipů;
- limit platí do konce killzone.
