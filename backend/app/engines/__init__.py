"""Decision engines.

Each engine takes NASA indicators + field info and returns one part of the
contract. Stage 1 ships a single `mock` engine; stage 2 splits into:

    risk.py         -> drought-risk score (0..100)
    water_budget.py -> available vs. needed water
    planting.py     -> plant now / wait / switch
    rotation.py     -> safest / balanced / highest-yield ranking
    copilot.py      -> Claude explanation layer (never invents, only explains)
"""
