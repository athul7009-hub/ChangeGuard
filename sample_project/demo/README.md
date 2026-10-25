# Shop Demo Sample Project

A tiny Python project for testing ChangeGuard's dependency analysis.

## Files
- `main.py` imports and uses `pipeline.py`.
- `pipeline.py` imports `pricing.py` and `inventory.py`.
- `pricing.py` imports `tax.py`.
- `tests/test_pricing.py` imports `pricing.py`.

## Try this in ChangeGuard
1. Load this folder using its full path.
2. Select `tax.py`. Expected affected files include `pricing.py`, `pipeline.py`, and `main.py`.
3. Select `inventory.py`. Expected affected files include `pipeline.py` and `main.py`.
4. Select `main.py`. It should have no downstream affected files in this small graph.
