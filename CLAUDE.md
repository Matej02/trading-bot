# Trading bot – pokyny pro Claude

## Znalosti projektu = Obsidian vault `znalosti/`
Vault je „mozek“ projektu: propojené poznámky o výzkumu, strategiích, konceptech, metodice, infrastruktuře a trzích.
Uživatel ho čte a upravuje v Obsidianu; jsou to obyčejné .md soubory, změny vidíme oba hned.

**Před prací** (výzkum, nová strategie, změna bota, rozbor exportu):
1. Přečti `znalosti/00 Rozcestník.md` a poznámky, které se úkolu týkají (koncepty, předchozí výzkum, `Výzkum/Co nefunguje.md`).
2. Zkontroluj `znalosti/Od uživatele/` – co uživatel poslal nebo dopsal (a sekce, které vyplňuje sám, např. „Jak je kreslí uživatel“).
3. Neopakuj testy, které už ve vaultu mají výsledek, ledaže se mění data nebo pravidla – a řekni proč.
4. **Obrázky vždy taky, nejen text:** obrázky vložené v přečtených poznámkách (`![[...]]`) otevři a prohlédni (Read na soubor
   v `Přílohy/`). U FM mentorů a konceptů projdi jejich galerii `FM/Obrázky/FM obrázky – <sekce>.md` – u velké galerie aspoň
   lekce, které se úkolu týkají – a uživateli řekni, které obrázky jsi viděl.
5. **Před testem strategie projdi VŠE k ní:** celý text i všechny obrázky galerie daného mentora / konceptu (všechny lekce,
   ne výběr) a navazující koncepty ze Základů. Pravidla testu z toho sepiš bod po bodu s odkazem na lekci a stranu, ať je
   test co nejvěrnější originálu. Co z materiálu nejde přesně zjistit, napiš jako předpoklad a řekni to uživateli.

**Po práci:**
1. Nový výzkum = poznámka ve `Výzkum/` (plán, data, výsledek, závěr) propojená [[odkazy]] na koncepty, trhy a metodiku.
2. Aktualizuj dotčené poznámky (koncepty – sekce „Otestováno“, `Co nefunguje`, strategie, `00 Rozcestník`).
3. Každý materiál nebo export od uživatele → `Od uživatele/` + řádek do `Požadavky a nápady uživatele.md`; soubory do `Přílohy/`.
4. Nové koncepty podle `Koncepty/Šablona konceptu.md`, zapsat do `Koncepty/Databáze konceptů.md`.
5. Odkazy musí vést na existující poznámky (název souboru bez .md).
6. Grafy a obrázky (z testů, od uživatele) ulož do `Přílohy/` a vlož do poznámky (`![[...]]`), ne je jen popsat textem.

## Pravidla
- Klíče a hesla nikdy nechtít ani neposílat; Vercel nastavuje uživatel. Jen demo / simulace. Vše zdarma.
- Všechno ukládat na disk D (`D:\Trading bot`, pomocné soubory `scratch/`).
- Výzkum s plánem předem, náklady brokera, odděleným ověřovacím obdobím a porovnáním s náhodnými vstupy.
