"""
Risk management vrstva - nezavisla na strategii.
Ukolem je hlidat, aby zadny jednotlivy trade ani spatny den/tyden
nemohl porusit pravidla prop firmy. Tohle bezi VZDY, bez ohledu na to,
co si strategie "preje" udelat.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class RiskConfig:
    starting_balance: float = 100_000.0
    risk_per_trade_pct: float = 0.5       # % uctu riskovaneho na jeden trade
    max_daily_loss_pct: float = 4.0       # tvrdy limit - typicka prop firma ma 4-5 %
    max_total_drawdown_pct: float = 8.0   # tvrdy limit - typicka prop firma ma 8-10 %
    profit_target_pct: float = 8.0        # cil pro splneni challenge
    max_trades_per_day: int = 4
    loss_cooldown_bars: int = 0           # po prohre pockat N baru, nez zkusit dalsi vstup (0 = vypnuto)


class RiskManager:
    def __init__(self, config: RiskConfig):
        self.cfg = config
        self.balance = config.starting_balance
        self.equity_peak = config.starting_balance
        self.current_day: date | None = None
        self.day_start_balance = config.starting_balance
        self.trades_today = 0
        self.halted = False
        self.halt_reason = ""
        self.challenge_passed = False
        self.cooldown_remaining = 0

    def new_bar(self, timestamp):
        """Zavolat na zacatku kazdeho baru - resetuje denni pocitadla."""
        bar_date = timestamp.date()
        if self.current_day != bar_date:
            self.current_day = bar_date
            self.day_start_balance = self.balance
            self.trades_today = 0
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

    def can_trade(self) -> bool:
        if self.halted or self.challenge_passed:
            return False
        if self.trades_today >= self.cfg.max_trades_per_day:
            return False
        if self.cooldown_remaining > 0:
            return False
        return True

    def position_size(self, sl_distance_price: float, pip_value_per_lot: float, pip_size: float,
                       risk_pct_override: float = None) -> float:
        """Vypocita velikost pozice (v lotech) tak, aby ztrata pri zasazeni SL
        odpovidala presne risk_per_trade_pct kapitalu (nebo risk_pct_override,
        kdyz je zadany - napr. pro portfolio, kde ma kazdy system jinou
        alokaci rizika ze sdileneho uctu)."""
        pct = risk_pct_override if risk_pct_override is not None else self.cfg.risk_per_trade_pct
        risk_amount = self.balance * (pct / 100)
        sl_pips = sl_distance_price / pip_size
        if sl_pips <= 0:
            return 0.0
        loss_per_lot = sl_pips * pip_value_per_lot
        if loss_per_lot <= 0:
            return 0.0
        lots = risk_amount / loss_per_lot
        return max(round(lots, 2), 0.01)

    def register_trade_result(self, pnl: float):
        self.balance += pnl
        self.trades_today += 1
        self.equity_peak = max(self.equity_peak, self.balance)
        if pnl < 0:
            self.cooldown_remaining = self.cfg.loss_cooldown_bars
        self._check_limits()

    def refresh_from_broker(self, balance: float, equity_peak: float, day_start_balance: float,
                             trades_today: int, cooldown_active: bool = False):
        """Synchronizuje stav se skutecnym uctem (live/demo obchodovani).
        Broker je jediny zdroj pravdy o balance a historii obchodu -
        na rozdil od backtestu tady nic lokalne nescitame, protoze
        lokalni pocitadla by po restartu skriptu byla nespolehliva."""
        self.balance = balance
        self.equity_peak = max(equity_peak, balance)
        self.day_start_balance = day_start_balance
        self.trades_today = trades_today
        self.cooldown_remaining = self.cfg.loss_cooldown_bars if cooldown_active else 0
        self._check_limits()

    def _check_limits(self):
        daily_loss_pct = (self.day_start_balance - self.balance) / self.cfg.starting_balance * 100
        drawdown_pct = (self.equity_peak - self.balance) / self.cfg.starting_balance * 100
        profit_pct = (self.balance - self.cfg.starting_balance) / self.cfg.starting_balance * 100

        if daily_loss_pct >= self.cfg.max_daily_loss_pct:
            self.halted = True
            self.halt_reason = f"Prekrocen max denni loss limit ({daily_loss_pct:.2f}%)"
        elif drawdown_pct >= self.cfg.max_total_drawdown_pct:
            self.halted = True
            self.halt_reason = f"Prekrocen max drawdown limit ({drawdown_pct:.2f}%)"
        elif profit_pct >= self.cfg.profit_target_pct:
            self.challenge_passed = True
