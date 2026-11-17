# Launch-Day Lens — GTA VI Twitch CCU Forecaster

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/ndus/makefun-gta6-forecast/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/ndus/makefun-gta6-forecast/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

Entry for the make.fun competition **gta6-twitch-ccu-forecast-01** ("Forecast GTA VI's launch-day Twitch viewers hour by hour"): a program that reads everything recorded up to the end of hour 1 of release day (2026-11-19, UTC) and forecasts the Twitch concurrent viewers of the Grand Theft Auto VI category for each of hours 2–24, as five quantiles (5%, 25%, 50%, 75%, 95%) per hour. Scored by pinball loss on the log scale; lowest wins.

## Method

The case file carries the full release-day curves of dozens of comparable past game launches. For each comparable, the program forms the log-ratios ln(viewers in hour h / viewers in hour 1) of its release day, then pools them per forecast hour with a Gaussian kernel weight on the distance between the comparable's hour-1 audience and this case's hour-1 print — launches of a similar size bend the forecast most. The five quantiles of that weighted pool, per hour, become the forecast: q_tau(h) = p1 · exp(Q_tau(h)). Hours pool their immediate neighbours (h−1, h, h+1) so the 5% and 95% tails rest on more than a handful of launches. If a case carries no usable comparables, the program falls back to persistence with a widening lognormal spread.

The program is a single `main.py` (Python 3.13, standard library only), deterministic, offline, and runs in well under the 8-second per-case cap.
