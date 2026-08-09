# Korea KOSPI200 Company Analysis Demo

🇰🇷 [한국어](README.md) · 🇬🇧 English

A tool that shows, at a glance, the financial condition and market mood of the
large-cap companies that have been part of Korea's KOSPI200 (321 companies
over 10 years, delisted ones included). Pick a stock and it displays financial
health + market state + a combined interpretation. It is a demo for
demonstration purposes that also shows the model's limitations honestly.

> ⚠️ **This system is a demo for demonstration purposes. Do not use it for actual investing.**

![Dashboard overview](docs/images/overview.png)

---

## What does it show?

1. **Per-stock analysis** — financial health + market state + combined
   interpretation for a company of interest (e.g., Samsung Electronics)
2. **Market state** — the Korean market's mood over time (risk-off / neutral /
   risk-on)
3. **Limitations page** — the model's honest limitations, clearly marked as a demo

Everything is laid out with charts and cards on a dark, financial-report-toned
screen.

![Per-stock analysis screen](docs/images/ticker_analysis.png)

![Market state screen](docs/images/market_state.png)

---

## How was it built?

A project built together with Claude.

- Uses financial statements and price data for the 321 companies that were in
  the KOSPI200 during the analysis period (2015–2024)
- Machine-learning models produce the risk score and the market-state
  classification
- The language model (LLM) is used *only as a writing aid that phrases
  already-validated numbers in line with the market state* — it decides no
  numbers. Interpretation sentences are generated once at build time and
  frozen; nothing is called while the web page is running. They currently
  exist for the top 40 stocks by market cap; the remaining stocks show
  template sentences.
- Results are displayed as a web page (Streamlit)

For technical details, see the [methodology document](docs/methodology.md) and
the model cards in [`reports/`](reports/).

---

## Why is it built this way? — Design Q&A

**Q. Why show financial analysis together with the market state?**
Because we believe the same financial change should be read differently
depending on the market mood. For example, the same increase in debt deserves
more caution in a risk-off market. That is why the interpretation sentences
are generated conditionally on the market state.

**Q. Why include delisted companies (321 in total)?**
Looking only at the stocks that survived removes failure cases from the
sample — *survivorship bias*. So we combine the quarterly point-in-time
KOSPI200 membership with the stocks delisted during the analysis period, and
look at *"the companies that were in the KOSPI200 at that point in time"* as
they were.

**Q. Why is the language model (LLM) run only once, in advance?**
The numbers are decided by the machine-learning and statistics layer; the LLM
only serves as a writing aid that phrases already-validated numbers in Korean.
Generating once at build time and freezing the output makes costs predictable
and results reproducible, and CI verifies that the running web page makes
zero LLM calls.

**Q. Why Python?**
Because every stage — data collection (DART, pykrx, FinanceDataReader), model
training (scikit-learn, LightGBM, hmmlearn), and the web screen (Streamlit) —
can be chained together within a single language's ecosystem.

**Q. Why batch analysis of historical data instead of real time?**
This system is a demo, so reproducibility of results comes first. Real-time
processing, precise price prediction, and trading were ruled out of scope from
the start.

**Q. The model's performance is poor — why show it as is?**
The risk model's performance (PR-AUC) came out below the random baseline. This
is quantitative evidence of the limits of a population like the KOSPI200,
where distress events are rare — so instead of hiding it, we recorded it as is
in the model card and the limitations page.

---

## How to run

```bash
# Set up the environment
uv sync --frozen

# API key
cp .env.example .env
# fill in DART_API_KEY=...

# Collect data
uv run python scripts/collect_data.py

# Train models
uv run python scripts/train_d2_baseline.py
uv run python scripts/train_regime.py

# (Optional) Generate interpretation sentences — add GEMINI_API_KEY to .env first.
# Safe to skip (those stocks fall back to template sentences).
uv run python scripts/generate_interpretations.py --scope latest --order marcap --limit 40

# Run the web page
uv run streamlit run app/main.py
```

---

## Environment

- Python 3.13
- Korean-language web page
- Desktop browser recommended

---

## License

[MIT](LICENSE)

---

🤖 A project built together with Claude (work in progress).
