MACRO_EVENTS = [
    # FOMC
    {"date":"2020-03-03","name":"Fed Emergency Cut -50bps","category":"FOMC"},
    {"date":"2020-03-15","name":"Fed Emergency Cut -100bps + QE","category":"FOMC"},
    {"date":"2022-03-16","name":"Fed Hike +25bps — First hike since 2018","category":"FOMC"},
    {"date":"2022-05-04","name":"Fed Hike +50bps","category":"FOMC"},
    {"date":"2022-06-15","name":"Fed Hike +75bps","category":"FOMC"},
    {"date":"2022-07-27","name":"Fed Hike +75bps","category":"FOMC"},
    {"date":"2022-09-21","name":"Fed Hike +75bps","category":"FOMC"},
    {"date":"2022-11-02","name":"Fed Hike +75bps","category":"FOMC"},
    {"date":"2022-12-14","name":"Fed Hike +50bps","category":"FOMC"},
    {"date":"2023-02-01","name":"Fed Hike +25bps","category":"FOMC"},
    {"date":"2023-03-22","name":"Fed Hike +25bps","category":"FOMC"},
    {"date":"2023-05-03","name":"Fed Hike +25bps — possibly last","category":"FOMC"},
    {"date":"2023-09-20","name":"Fed Hold at 5.25–5.50%","category":"FOMC"},
    {"date":"2023-11-01","name":"Fed Hold","category":"FOMC"},
    {"date":"2024-09-18","name":"Fed Cut -50bps","category":"FOMC"},
    {"date":"2024-11-07","name":"Fed Cut -25bps","category":"FOMC"},
    {"date":"2024-12-18","name":"Fed Cut -25bps — hawkish signal","category":"FOMC"},
    {"date":"2025-01-29","name":"Fed Hold — cautious on inflation","category":"FOMC"},
    # CPI
    {"date":"2021-06-10","name":"CPI +5.0% YoY — highest since 2008","category":"CPI"},
    {"date":"2021-11-10","name":"CPI +6.2% YoY — 30-year high","category":"CPI"},
    {"date":"2022-01-12","name":"CPI +7.0% YoY","category":"CPI"},
    {"date":"2022-06-10","name":"CPI +8.6% YoY — 40-year peak","category":"CPI"},
    {"date":"2022-09-13","name":"CPI +8.3% YoY — hotter than expected","category":"CPI"},
    {"date":"2023-01-12","name":"CPI +6.5% YoY — disinflation begins","category":"CPI"},
    {"date":"2023-06-13","name":"CPI +4.0% YoY","category":"CPI"},
    {"date":"2024-02-13","name":"CPI +3.1% — hotter than forecast","category":"CPI"},
    {"date":"2024-09-11","name":"CPI +2.5% — near target","category":"CPI"},
    {"date":"2025-02-12","name":"CPI +3.0% — sticky inflation","category":"CPI"},
    # RBI
    {"date":"2020-03-27","name":"RBI Emergency Cut -75bps","category":"RBI"},
    {"date":"2022-05-04","name":"RBI Off-cycle Hike +40bps","category":"RBI"},
    {"date":"2022-06-08","name":"RBI Hike +50bps","category":"RBI"},
    {"date":"2023-04-06","name":"RBI Hold at 6.50%","category":"RBI"},
    {"date":"2024-04-05","name":"RBI Hold — stance changed to neutral","category":"RBI"},
    {"date":"2024-10-09","name":"RBI Hold at 6.50%","category":"RBI"},
    {"date":"2025-02-07","name":"RBI Cut -25bps to 6.25%","category":"RBI"},
    # Geopolitical
    {"date":"2020-02-24","name":"COVID-19 market panic begins","category":"Geopolitical"},
    {"date":"2020-03-11","name":"WHO declares COVID-19 pandemic","category":"Geopolitical"},
    {"date":"2022-02-24","name":"Russia invades Ukraine","category":"Geopolitical"},
    {"date":"2023-03-10","name":"Silicon Valley Bank collapse","category":"Geopolitical"},
    {"date":"2023-10-07","name":"Hamas attack on Israel","category":"Geopolitical"},
    {"date":"2024-08-05","name":"Global market crash — Yen carry unwind","category":"Geopolitical"},
    {"date":"2025-01-20","name":"Trump inauguration — tariff fears","category":"Geopolitical"},
]

def get_events(category: str = None) -> list:
    if category:
        return [e for e in MACRO_EVENTS if e["category"] == category]
    return MACRO_EVENTS
