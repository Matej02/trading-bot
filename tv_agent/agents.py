"""
Agenti, kteri posuzuji signal pred vstupem. Kazdy vraci Verdict s duvodem.
Pipeline spousti VSECHNY (i kdyz uz nekdo vetoval), aby byl denik uplny
a dalo se pozdeji zjistit, ktery agent jak casto a jak spravne vetuje.

Agenti 1-4 jsou kod: jdou otestovat na historii a davaji pokazde stejnou
odpoved. LLM agenti (zpravy, dabluv advokat) prijdou az s API klicem.

Cas: MT5 vraci casy v case serveru brokera. Agenti dostavaji posun
server_offset_h (server = UTC + posun), aby hodiny sedely.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import mt5_connector


@dataclass
class Verdict:
    agent: str
    approve: bool
    reason: str
    data: dict = field(default_factory=dict)


class ValidatorAgent:
    """1) Je signal cerstvy, neutekla cena, neni to duplicita?"""
    name = "validator"

    def __init__(self, pip_cache, max_age_s=900, max_drift_pips=3.0):
        self.pip_cache = pip_cache
        self.max_age_s = max_age_s
        self.max_drift_pips = max_drift_pips
        self.seen = set()

    def check(self, s):
        if s.id in self.seen:
            return Verdict(self.name, False, f"duplicitni signal {s.id}")
        self.seen.add(s.id)

        age = (datetime.now(timezone.utc) - s.time).total_seconds()
        if age > self.max_age_s:
            return Verdict(self.name, False, f"signal je stary {age/60:.0f} min (limit {self.max_age_s/60:.0f})",
                           {"age_s": age})

        pip = self.pip_cache[s.symbol][0]
        bid, ask, _ = mt5_connector.get_current_prices(s.symbol)
        now_px = ask if s.direction == "long" else bid
        # kladny drift = vstup je ted drazsi nez v okamziku signalu
        drift = ((now_px - s.price) if s.direction == "long" else (s.price - now_px)) / pip
        if drift > self.max_drift_pips:
            return Verdict(self.name, False, f"cena utekla o {drift:.1f} pipu (limit {self.max_drift_pips})",
                           {"drift_pips": drift})
        return Verdict(self.name, True, f"cerstvy ({age:.0f} s), drift {drift:+.1f} pipu",
                       {"age_s": age, "drift_pips": drift})


class MarketNowAgent:
    """2) Da se v tuhle chvili rozumne obchodovat? Spread, rollover, vikend."""
    name = "trh_ted"

    def __init__(self, pip_cache, normal_spread, server_offset_h=0, max_ratio=2.0,
                 forbidden_utc_hours=(21, 22), friday_cutoff_utc=19, holds_weekends=()):
        self.pip_cache = pip_cache
        # normal_spread: {symbol: {hodina_serveru: median_pipu}}
        self.normal = {sym: {int(h): v for h, v in hrs.items()} for sym, hrs in normal_spread.items()}
        self.offset = server_offset_h
        self.max_ratio = max_ratio
        # 21:00 UTC = NY rollover v letnim case, 22:00 UTC v zimnim - blokujeme obe
        self.forbidden = set(forbidden_utc_hours)
        self.friday_cutoff = friday_cutoff_utc
        # setupy, ktere drzi tydny (momentum) - patecni pravidlo proti gapu pro ne nema smysl
        self.holds_weekends = set(holds_weekends)

    def check(self, s):
        now = datetime.now(timezone.utc)
        if now.weekday() >= 5:
            return Verdict(self.name, False, "vikend - trh zavreny")
        if now.weekday() == 4 and now.hour >= self.friday_cutoff and s.setup not in self.holds_weekends:
            return Verdict(self.name, False, "patek vecer - riziko gapu pres vikend")
        if now.hour in self.forbidden:
            return Verdict(self.name, False, f"rollover okno ({now.hour}:00 UTC) - spread tu skace na 4-20 pipu")

        pip = self.pip_cache[s.symbol][0]
        _, _, sp = mt5_connector.get_current_prices(s.symbol)
        sp_pips = sp / pip
        server_hour = (now + timedelta(hours=self.offset)).hour
        normal = self.normal.get(s.symbol, {}).get(server_hour)
        data = {"spread_pips": sp_pips, "normal_pips": normal}
        if normal and sp_pips > self.max_ratio * normal:
            return Verdict(self.name, False,
                           f"spread {sp_pips:.1f} pipu je {sp_pips/normal:.1f}x nad normalem ({normal:.1f})", data)
        return Verdict(self.name, True,
                       f"spread {sp_pips:.1f} pipu (normal {normal:.1f})" if normal else f"spread {sp_pips:.1f} pipu",
                       data)


class StatisticianAgent:
    """3) Ma tenhle setup na tomhle symbolu overenou edge? Bez overeni veto.

    Registr (setups.json) se plni VYHRADNE vysledky testu se spready a
    holdoutem - ne odhadem. Tim agent brani tomu, aby se obchodovalo na
    neco, co jen dobre zni.
    """
    name = "statistik"
    MIN_PF = 1.10
    MIN_N = 100

    def __init__(self, registry_path):
        with open(registry_path, encoding="utf-8") as f:
            self.reg = json.load(f)

    def check(self, s):
        setup = self.reg.get(s.setup, {})
        rec = setup.get(s.symbol) or setup.get("*")          # "*" = plati pro vsechny trhy setupu
        if not rec:
            return Verdict(self.name, False, f"setup '{s.setup}' na {s.symbol} neni v registru - neovereny")
        if rec.get("status") != "validated":
            return Verdict(self.name, False, f"neovereno: {rec.get('note', '')}", rec)
        if rec.get("holdout_pf", 0) < self.MIN_PF or rec.get("holdout_n", 0) < self.MIN_N:
            return Verdict(self.name, False,
                           f"slaba evidence: PF {rec.get('holdout_pf')} / n {rec.get('holdout_n')} "
                           f"(minimum PF {self.MIN_PF}, n {self.MIN_N})", rec)
        return Verdict(self.name, True, f"overeno: holdout PF {rec['holdout_pf']}, n {rec['holdout_n']}", rec)


class RiskAgent:
    """4) Unese ucet dalsi obchod? Limity prop firmy + expozice na menu."""
    name = "risk"

    def __init__(self, rm, starting_balance, challenge_start, max_currency_exposure=2):
        self.rm = rm
        self.starting_balance = starting_balance
        self.challenge_start = challenge_start
        self.max_exp = max_currency_exposure

    def check(self, s):
        bal, peak, dsb, tt, cd = mt5_connector.compute_risk_state_from_history(
            self.starting_balance, self.challenge_start, cooldown_bars=self.rm.cfg.loss_cooldown_bars)
        self.rm.refresh_from_broker(bal, peak, dsb, tt, cooldown_active=cd)
        data = {"balance": bal, "peak": peak, "trades_today": tt}
        if self.rm.halted:
            return Verdict(self.name, False, f"zastaveno: {self.rm.halt_reason}", data)
        if not self.rm.can_trade():
            return Verdict(self.name, False, f"limit obchodu nebo cooldown (dnes {tt}, cooldown {cd})", data)

        exp = self._exposure(extra=s)
        data["expozice"] = exp
        worst = max(exp.items(), key=lambda kv: abs(kv[1]), default=(None, 0))
        if abs(worst[1]) > self.max_exp:
            return Verdict(self.name, False,
                           f"prilis velka expozice na {worst[0]} ({worst[1]:+d} pozic stejnym smerem)", data)
        return Verdict(self.name, True, f"balance {bal:.0f}, dnes {tt} obchodu, expozice OK", data)

    def _exposure(self, extra=None):
        """Cista expozice na jednotlive meny: long EURUSD = +EUR, -USD.
        Jen forex a kovy - index, ropa ani krypto nejsou sazka na menu."""
        exp = {}

        def add(symbol, is_long):
            si = mt5_connector.mt5.symbol_info(symbol)
            if si is None or si.path.split("\\")[0] not in ("FOREX", "METALS"):
                return
            base, quote = si.currency_base, si.currency_profit
            sign = 1 if is_long else -1
            exp[base] = exp.get(base, 0) + sign
            exp[quote] = exp.get(quote, 0) - sign

        for p in (mt5_connector.mt5.positions_get() or []):
            add(p.symbol, p.type == mt5_connector.mt5.POSITION_TYPE_BUY)
        if extra is not None:
            add(extra.symbol, extra.direction == "long")
        return exp
