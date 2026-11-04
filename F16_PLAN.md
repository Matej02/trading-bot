# F16 – Hakimi: PDF + obrázky jako zdroj, B5 jako dodatek (plán předem, 2026-11-04)

Zdroje:
- celý text 29 PDF (`scratch/fm/hakimi_vse.txt`);
- všech 125 obrázků (`FM/Obrázky/FM obrázky – Sunita Hakimi (day).md`, [obr N]);
- Word B5 jen jako dodatek („Elliott na kovy a krypto, orientuje se podle zón, ne sessions“).

## Pravidla
1. **Směr:** trend H4 (2 vyšší high + 2 vyšší low, pivot N 2) = směr impulzu [PDF Uptrend vs Downtrend, MTF, obr 82–91].
2. **Vlny (Elliott) mechanicky** [PDF Elliott teorie/praxe, obr 8–21, 119–123]:
   - ZigZag na zavíracích cenách 15m (otočka 2 ATR 15m);
   - **vlna 1** = noha ve směru H4, která prorazí předchozí swing (BOS);
   - **vlna 2** = pullback, který nesmí jít za začátek vlny 1 (pravidlo 1).
   - Varianta `vlna4`: totéž pro vlnu 4 (pullback po vlně 3, která je delší než vlna 1, a nesmí zasáhnout do vlny 1 – pravidlo 3).
3. **Zóna vstupu** = průnik konfluencí [PDF Entry model, obr 119–121]:
   - Fibo vlny 1 (zleva doprava) pásmo 0,618–0,75 [PDF Fibo; obr 37–44];
   - varianta `zona`: 15m S/D zóna (FM pravidla: impulzivní svíčka po zóně, BOS) v pásmu [PDF SD HTF/LTF];
   - varianta `fvg`: FVG z vlny 1 v pásmu (reakce od 50 %) [PDF FVG].
4. **Vstup** (varianta):
   - `limit` na horní hraně pásma / zóny;
   - `potvrz`: 15m svíčka zavře zpět nad 0,618 po doteku pásma (reakce) → trhem [PDF Entry model „reakce na“].
5. **SL** [obr 119–121, PDF Elliott „SL za vlnu 2“]:
   - `zona`: pod spodní hranou zóny / 0,75 − 0,1 ATR;
   - `vlna`: pod začátkem vlny 1.
6. **TP** [obr 119–121]:
   - `loc`: high vlny 1 (LOC likvidita);
   - `ext`: 1,618 extenze vlny 1 (cíl vlny 3).
   **RR ≥ 2,5** [PDF Risk reward], jinak obchod ne (strop 8 R). **Bez BE** [PDF Breakeven].
7. Bez session filtru [B5]. Konec dne 22:00 Praha (day trading). Bez dní FOMC a NFP (Core PPI nemáme) [PDF News trading].
8. **Trhy:** XAUUSD, XAGUSD (hlavní) + varianta EURUSD, GBPUSD, NAS100 („upravená verze na forex a NQ“). MT5 M1, vývoj do 2021, OOS 2022–26.
   Výběr varianty jen na vývoji na XAU+XAG, pak ověření na ostatních.

## Předpoklady
- ZigZag 2 ATR 15m jako náhrada ručního počítání vln;
- trendový kanál a nPOC nejsou kódem (jen jako cíl ve variantě by nPOC šel – vynecháno);
- „reakce“ = zavření zpět nad 0,618.
