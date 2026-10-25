# Solactive AI Index – public daily data

This repository publishes verified daily values for the Solactive US Artificial Intelligence (AI) Index (NTR), ISIN **DE000SL0K4X5**.

Source: https://www.solactive.com/index/DE000SL0K4X5/

The workflow at `.github/workflows/solactive-daily.yml` calls Solactive's day-history POST endpoint, validates the data, and commits generated JSON to `data/`. It runs daily at 09:17 and 09:42 (Europe/Helsinki) and can also be started manually in **Actions → Update Solactive AI index → Run workflow**.

Published JSON files:
- [Latest value and changes](data/solactive-summary.json)
- [Last 30 trading days](data/solactive-30d.json)
- [Last 12 months](data/solactive-12m.json)
- [All available history](data/solactive-history.json)

Public raw URLs follow: `https://raw.githubusercontent.com/Zymymenestys/solactive-ai-data/main/data/<filename>`

Verify `observed_through` and `retrieved_at_utc` before treating a value as current. A failed fetch must not overwrite previous verified data. GitHub's scheduled jobs are best-effort and can be delayed. Repo data is public.

This tracks the **index only**; Leverage Shares GPTS AUM comes from the issuer's website.
