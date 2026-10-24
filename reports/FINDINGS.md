# Findings

Scope for every finding: the **global sample** of news-reported layoffs (5,000 events at 3,467 companies, 1 Jan 2019 – 14 Jun 2026), a 26% company-cluster sample of 19,208 events (Fliar Research, CC BY-NC 4.0). Counts are sample counts, not market totals. Job figures are disclosed cuts only (lower bounds). 2026 runs to 14 June only. Nothing here is causal.

---

### 1. Layoff activity has stayed well above the 2019 level since 2023

- **Observed.** 476 events in 2019; 968 in 2020; 265 in 2021; 525 in 2022; 885 in 2023, 791 in 2024 and 762 in 2025 (sample counts).
- **Evidence.** Query 02; Power BI page 1 "Events per year with 90% interval"; notebook 05 bootstrap.
- **Period and denominator.** Calendar years 2019–2025 (2026 excluded as partial); all 5,000 global events.
- **Uncertainty.** 90% company-cluster intervals: 2019 437–515, 2023 834–936, 2024 742–840, 2025 710–813. Every 2023–2025 interval sits far above 2019's. Event counts track the full data within about ±1 percentage point (sample ÷ full 0.256–0.271), so the pattern generalises to the source. 2020's peak depends on furloughs: without the 105 furlough events, 2020 has 863, just below 2023.
- **Decision it supports.** Treat 2023–2025 as a sustained higher baseline when planning, not a one-off spike. It does not support a forecast for 2026.

### 2. Disclosed job totals cannot rank 2023–2025

- **Observed.** Disclosed jobs: 2023 ≈ 423k, 2024 ≈ 434k, 2025 ≈ 417k (sample, lower bounds).
- **Evidence.** Query 02; notebook 05 benchmark and bootstrap; Power BI page 4 "Sample coverage vs the full data".
- **Uncertainty.** 90% intervals overlap (~306k–565k). The sample-to-full ratio for disclosed jobs swings from 0.225 to 0.341 by year, and the full data orders these years 2023 > 2025 > 2024. Only "2020 had the most disclosed cuts" survives (lower bound 553k, above every other year's upper bound).
- **Decision it supports.** Report events, not job totals, for year-to-year comparisons. Never quote a sample job sum as a total.

### 3. Most disclosed layoffs are small; a few very large ones dominate job totals

- **Observed.** Of 2,489 events with a disclosed headcount, 69.5% cut fewer than 500 people (1–99: 31.1%; 100–499: 38.4%); 5.9% cut 5,000 or more. Median disclosed cut 200.
- **Evidence.** Query 08; Power BI page 1 card.
- **Denominator.** Events with a disclosed headcount (2,489 of 5,000).
- **Limitation.** Disclosure is not random: 55.3% in North America vs 41.3% in Latin America (`core.v_bi_quality`; Power BI page 4), so size figures over-represent well-reported regions.
- **Decision it supports.** Use the median, not the mean, to describe a "typical" layoff.

### 4. Retail & Consumer is the largest known industry group; Travel and Software had their own spikes

- **Observed.** Retail & Consumer 680 events (13.6%), Finance & Fintech 375 (7.5%). Travel & Transport was 8.4% of 2020 events vs 1.4% in 2023; Software & IT 9.9% in 2023 vs 3.3% in 2020.
- **Evidence.** Queries 03 and 04; Power BI page 2 (bar chart, 100% stacked chart, pie with year selector).
- **Limitation.** 31.3% of events have no industry ("Unknown" is shown, not hidden), so gaps between smaller groups are not reliable.
- **Decision it supports.** Sector monitoring should weight the industries named here, while noting a third of events cannot be assigned.

### 5. The US share of events with a known country rose after 2021

- **Observed.** 27.6% in 2021; 48.5% in 2023; 43.6–45.6% in 2024–2026.
- **Evidence.** Query 07; Power BI page 2 card (42.3% overall).
- **Denominator.** Events with a known country (9% have none).
- **Limitation.** Coverage of non-English news is unknown, so this may partly reflect where news is collected.

### 6. About 1 in 8 companies had another layoff within a year of their first

- **Observed.** 12.6% (95% CI 11.5–13.8%) within 12 months, 16.2% (14.9–17.5%) within 24 months. Median gap among repeaters 266 days. 688 of 3,467 sampled companies had 2+ events (19.8%; full data 20.8%).
- **Evidence.** Notebook 05 Kaplan–Meier; Power BI page 3 curve and cards; query 15/16 for counts.
- **Uncertainty and limits.** Right-censored at 14 Jun 2026; left-truncated at 2019; the source merges reports within 45 days; split brand names hide some repeats.
- **Group differences.** 12-month repeat: 17.9% after a first cut of 500+, 14.3% under 500, 10.5% when undisclosed (log-rank p < 0.001; the 500+ and under-500 intervals overlap). No difference by era (p ≈ 0.97). Among the 16 known industries no significant difference (p ≈ 0.13).
- **Decision it supports.** A first disclosed layoff is a meaningful signal that another round may follow within a year for roughly 1 in 7 to 1 in 6 such companies. Do not rank industries by repeat risk.

---

**What the data cannot answer:** total jobs lost; layoff rates (no company size); causes; AI's share; which company will cut next.
