# Decision-aware RankCert follow-up

Exploratory analysis of internal discarded-weight surrogates and multi-setting
ranking stability. It reads the completed `results/rankcert_mps` namespace as
an immutable input and writes only to `results/decisioncert_mps`.

Nothing produced here is promoted to a mathematical certificate.

```powershell
& 'C:\Users\psgpe\Downloads\Taiwan\.venv\Scripts\python.exe' `
  .\experiments\decisioncert_mps\analyze_decisioncert.py
```
