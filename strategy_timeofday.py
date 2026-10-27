"""
Time-of-day strategie: jediny pristup, ktery v tomhle projektu prosel
poctivym out-of-sample testem (vyber 2016-2022, overeni 2023-2026).

Princip: forex ma strukturalni denni cyklus (likvidita, fixingy, rollover).
Nektere hodiny maji stabilni smerovy sklon. Neobchoduje se zadny vzor v
grafu - jen se v presne dany cas otevre pozice a po N hodinach zavre.

DULEZITE - casovani:
  Svicka s hodinou H se UZAVIRA v H+1:00. Setup "bar_hour=22" tedy
  znamena vstup ve 23:00 UTC.

VYLOUCENO: vstup ve 21:00 a 22:00 UTC. V tom okne spread skace na
4-20 pipu (rollover) a jakykoliv "efekt" tam je artefakt, ne prilezitost.

Konkretni setupy jsou v SETUPS - plni se z vysledku vyzkumu, ne odhadem.
Kazdy ma vlastni magic cislo kvuli sledovani pozic.
"""

from dataclasses import dataclass


@dataclass
class TodSetup:
    symbol: str
    entry_hour_utc: int      # kdy se otevira pozice (UTC)
    hold_hours: int          # po kolika hodinach zavrit
    direction: str           # "long" / "short"
    magic: int
    expected_edge_pips: float   # ocekavana hruba edge - pro porovnani s realitou
    expected_cost_pips: float   # ocekavany naklad (spread + skluz)

    @property
    def label(self) -> str:
        return f"{self.symbol}-{self.entry_hour_utc:02d}h-{self.direction}"

    @property
    def exit_hour_utc(self) -> int:
        return (self.entry_hour_utc + self.hold_hours) % 24


# !!! ZAMITNUTO 2026-08-26 - NEPOUZIVAT !!!
#
# Tick-presna rekonstrukce 1650 skutecnych obchodu (2024-09 az 2026-08,
# plneni na realnem bid/ask) ukazala, ze cele portfolio prodelava
# -19.3 % rocne (Sharpe -5.64). Duvody:
#   1) Spread v 23:00:00 je vyssi nez median za celou hodinu 23
#      (EURCAD skutecne 3.70 pipu round-trip vs odhadovanych 1.45)
#   2) Edge se v poslednich 2 letech rozpadla - pohyb mid ceny je
#      +1.11 az -0.29 pipu proti historickym +1.7 az +2.9
#
# Setupy nize zustavaji jen jako zaznam. Runner je nespousti.
#
# Puvodni poznamka k vyzkumu:
# 852 testovanych kombinaci (13 instrumentu x 22 hodin
# x 3 doby drzeni), vyber na 2016-2022 pri |t|>4, overeni na 2023-2026.
# Naklad = vstupni + vystupni spread (z tick dat) + skluz; zadny z techto
# setupu neprochazi rolloverem, takze neplati swap.
#
# Portfolio jako celek na holdoutu: rocni Sharpe 1.00, +3.62 %/rok pri
# 1 lotu na setup, max drawdown 6.54 %.
#
# Pri zmene VZDY nejdriv overit skriptem, ne odhadem.
SETUPS = [
    # --- hlavni: smysluplna edge i po nakladech ---
    TodSetup("EURCAD", entry_hour_utc=23, hold_hours=2, direction="long",
             magic=20260901, expected_edge_pips=2.88, expected_cost_pips=1.45),
    TodSetup("AUDJPY", entry_hour_utc=23, hold_hours=1, direction="long",
             magic=20260902, expected_edge_pips=1.71, expected_cost_pips=1.10),
    TodSetup("GBPJPY", entry_hour_utc=23, hold_hours=1, direction="long",
             magic=20260903, expected_edge_pips=2.40, expected_cost_pips=2.10),
    # --- doplnkove: edge po nakladech uz je v sumu (+0.07 az +0.08 pipu),
    #     drzeny hlavne kvuli diverzifikaci (koreluji jinak nez jenove pary)
    #     a kvuli sberu dat o plneni. Nesledovat u nich zisk. ---
    TodSetup("NZDUSD", entry_hour_utc=23, hold_hours=1, direction="long",
             magic=20260904, expected_edge_pips=1.66, expected_cost_pips=0.70),
    TodSetup("GBPUSD", entry_hour_utc=23, hold_hours=1, direction="long",
             magic=20260905, expected_edge_pips=2.02, expected_cost_pips=1.15),
]

FORBIDDEN_ENTRY_HOURS = {21, 22}
ROLLOVER_HOUR = 21          # zjisteno z tick dat: spread skace na 4-20 pipu


def crosses_rollover(setup) -> int:
    """Kolikrat pozice projde pres rollover (21:00 UTC).

    Kazdy pruchod znamena: zaplaceny swap + moznou zvysenou cenu vystupu.
    Prehlednuti tohohle je snadne a drahe - pri vyzkumu se prave setupy
    drzici pres rollover tvarily jako nejlepsi, dokud se swap nezapocital."""
    return sum(1 for k in range(1, setup.hold_hours + 1)
               if (setup.entry_hour_utc + k) % 24 == ROLLOVER_HOUR)


def validate_setups(setups=None):
    """Kontrola, ze zadny setup nevstupuje do rollover okna ani jim
    neprochazi bez vedomeho potvrzeni."""
    problems = []
    todo = setups if setups is not None else SETUPS
    for s in todo:
        if s.entry_hour_utc in FORBIDDEN_ENTRY_HOURS:
            problems.append(f"{s.label}: vstup v {s.entry_hour_utc}:00 je v rollover okne "
                            f"(spread 4-20 pipu) - zakazano")
        if s.hold_hours < 1:
            problems.append(f"{s.label}: hold_hours musi byt >= 1")
        if any(o is not s and o.magic == s.magic for o in todo):
            problems.append(f"{s.label}: duplicitni magic cislo {s.magic}")
        n = crosses_rollover(s)
        if n and not getattr(s, "rollover_ok", False):
            problems.append(
                f"{s.label}: pozice prochazi {n}x pres rollover ({ROLLOVER_HOUR}:00) - "
                f"plati se swap a vystupni spread je zvyseny. Pokud je to zamer, "
                f"nastav rollover_ok=True a overten, ze edge prezije i po swapu.")
    return problems
