# Review before sharing

Run the analysis and tests, then open the executed notebook and results.

Explain in your own words:

1. What is actually measured, and who collected the observations?
2. What units are used and where do conversions occur?
3. Why was this method chosen, and what is the comparison or baseline?
4. Which output supports the main finding?
5. What can the analysis not establish?
6. What additional data or validation would improve the project?

Supported CV sentence: Developed a reproducible Cameroon CO2 forecasting study using real emissions data, lagged predictors, rolling evaluation and baseline comparisons.

Main scope constraint: 65 annual observations; model settings are fixed rather than extensively tuned. Test results may favour a baseline. Forecasts are estimates, not known emissions, and do not support causal or clinical claims.

## Result you should be able to explain

Used **65 annual observations, 1960–2024**. Persistence was selected on the 2005–2014 validation period and also gave the lowest 2015–2024 test RMSE: **0.3835 Mt CO2**, compared with **0.7601** for Ridge and **0.8380** for random forest. Fixed model settings and the small dataset limit conclusions. The six-year projection stays at the last observed 2024 value, **9.632 Mt CO2/year**; it is an estimate, not an observation.
