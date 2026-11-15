"""Field Shift — AI/ML + data backend.

This package turns NASA Earth-observation data + local soil/crop info into the
decision contract defined in the Team Workflow doc (§8.6):

    FieldRequest  ->  Recommendation  (risk score, water budget,
                                       planting timeline, crop rotations,
                                       NASA indicators, AI explanation)

Stage 1 (now):  a *mock* engine returns realistic, internally-consistent
                numbers so the frontend can be built against the real contract.
Stage 2 (next): swap the mock for real NASA connectors + engines + ML + the
                Claude copilot, one module at a time, behind the same contract.
"""

__version__ = "0.1.0"
