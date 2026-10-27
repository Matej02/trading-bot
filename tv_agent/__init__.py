"""
Agentni obchodni bot pripraveny na TradingView.

Signal (Python pravidla nebo TradingView webhook) -> agenti posoudi ->
rozhodnuti -> MT5 (demo) -> denik vcetne ZAMITNUTYCH signalu.

Stinovy denik zamitnutych signalu je jadro celeho navrhu: jen diky nemu
jde zmerit, jestli agenti skutecne pomahaji, nebo jsou jen dekorace.
"""
