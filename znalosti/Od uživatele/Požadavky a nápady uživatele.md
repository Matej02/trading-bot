---
tags: [od-uzivatele, projekt]
aktualizovano: 2026-11-03
---
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
- 2026-10-29: Obsidian má fungovat jako společný mozek, ne jen složka ([[Jak spolupracujeme s Claude]]).
- 2026-10-29: **FM PDF, část 1 („dodatek“)** v `D:\youtube\FM pdfka`: přečíst a projít, zbytek pošle
  ([[FM materiály]], [[Databáze konceptů]]).
- 2026-10-29: projet **všechny** obrázky z FM PDF, prop firmy neřešit, backtestovat koncepty a strategie, S/D na vyšších TF ([[F8 Strategie z FM PDF]]).
- 2026-10-29: koncepty nechat, měnit jen strategii a kombinovat, dát na web a testovat live ([[F9 Kombinace FM konceptů]]).
- 2026-10-29: otestovat i Veselovského, Kimmela a Pátka, Word dokument už nepoužívat ([[F10 Entry modely mentorů FM]]).
- 2026-10-30: „není to možné, strategie lidem vydělávají“ → testovat pomalu, po jednom mentorovi, víc propojit věci ([[F11 Mentoři FM znovu a podrobně]]).
- 2026-10-30: prověřit a nainstalovat day-trader-skill ([[Day-trader skilly]]).
- 2026-11-01: obrázky mají být ve vaultu a při práci se mají kontrolovat i obrázky, ne jen text ([[Jak spolupracujeme s Claude]]).
- 2026-11-01: při testech projít **všechno** k dané strategii, ať je test co nejpřesnější.
- 2026-11-03: **doplňující pravidla k FM PDF** (obecná pravidla + mentoři, z Playbooku a odpovědí uživatele), pak testovat
  ([[Doplňující pravidla k FM PDF]]); export simulátoru za týden ([[Export simulátoru 2026-11-03]]); pošle ještě, co se stalo na live botovi.
- 2026-11-03: Word s doplňujícími pravidly je jen **dodatek**, hlavní zdroj jsou PDF a obrázky; vše testovat a dát live ([[F13 Veselovský podle PDF a doplňujících pravidel]], [[F14 Pátek podle PDF a doplňujících pravidel]]).
- 2026-11-04: souhlas se stažením COT z cftc.gov ([[F15 Hvězda podle PDF, doplňujících pravidel a COT]]).
- 2026-11-04: pokračovat Šrajer, Valchář, Kimmel; jako poslední krok vše nasadit a testovat live „na našem demu“ ([[FM live test na MT5 demu]]).
- 2026-11-04: po nasazení „hotovo pokračuj“ → poslední položka fronty, obecná strategie uživatele (část A) otestována v [[F20 Obecná strategie uživatele (SFP + FRVP)|F20]] a dána live na demo.
- 2026-11-05: runner přes noc neběžel, protože uživatel vypnul počítač. „Vše commitni, ať to můžeme live testovat na demu, vše zapiš; nevadí, že je repozitář otevřený, a pak pokračuj.“ → repozitář GitHub zůstává veřejný (rozhodnutí uživatele).
- 2026-11-07: „Do kdy budeme testovat, než dám reálné peníze na MetaTrader a zkusíme obchodovat live?“
  - Odpověď: demo neprokáže zisk, jen shodu provedení. Výhoda zatím u žádné strategie ověřená není.
  - Kritéria a čísla viz [[FM live test na MT5 demu#Kdy reálné peníze (2026-11-07)]].
- 2026-11-07: test F13 na delší historii (HistData 2010–2025, „nesahej na bota, dej si to vedle“) → bez výhody, viz [[F13 indexy na delší historii (HistData 2010–2025)|F13 na delší historii]].
  - Dotaz, zda z toho jde vytáhnout zlepšení: žádný řez obchodů není stabilní ve všech obdobích. Ponaučení je v metodě ověřování, ne ve filtru.
- 2026-11-07: „klidně zkus nový nápad, zase zapsat do vaultu mimo, dát vědět, jak to dopadlo, na bota nesahat“ → [[F21 Noční drift indexů (long přes noc)|F21]] noční drift US indexů: bez výhody (náhodné okno stejné délky lepší, US30 záporný).
- 2026-11-07: „rozepiš minimálně 10 dalších strategií, zatím jen rozpis, na bota stále nesahej“ → [[Fronta nápadů F22–F33]]. 12 nápadů, první vlna F22 ORB, F23 gap, F24 filtr volatility, F25 párové obchody.
- 2026-11-07: „nešlo by to udělat, že to otestuješ? A ne že to zapneme do bota?“ → jen testy, bot beze změny. První vlna F22–F25: vše bez výhody, viz [[Fronta nápadů F22–F33]].
- 2026-11-08: „pokračuj dál v testování strategií, zapisuj, ale nedávej je do bota, to si pak na konci zhodnotíme“ a „stáhni je klidně na D, dojeď všechny strategie a vypiš, které jsou navíc oproti botovi, a rozepiš výhody“ → [[Souhrn testů F21–F33 a přínosy]].
