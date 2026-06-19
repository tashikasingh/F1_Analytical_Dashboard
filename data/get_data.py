import fastf1
import pandas as pd

# get data from 2018 to 2026 (might have to do in batches as number of requests exceeds
# what is allowed by fastf1)
for year in range(2018, 2026):

    schedule = fastf1.get_event_schedule(year, include_testing=False)

    all_laps = []
    all_results = []
    all_qualifying = []
    all_qualifying_laps = []

    for _, event in schedule.iterrows():
        gp_name = event["EventName"]
        gp_round = event["RoundNumber"]

        print(f"\n  [{year}] {gp_name}...")

        # for laps data
        try:
            race = fastf1.get_session(year, gp_round, "R")
            race.load(laps=True, telemetry=False, weather=False, messages=False)

            laps = race.laps.copy()
            laps["RoundNumber"] = gp_round
            laps["EventName"] = gp_name
            laps["Season"] = year
            all_laps.append(laps)
        except Exception as e:
            print(f"Race laps: {e}")

        # for race results
        try:
            results = race.results.copy()
            results["RoundNumber"] = gp_round
            results["EventName"] = gp_name
            results["Season"] = year
            all_results.append(results)
        except Exception as e:
            print(f"Race results: {e}")

        # for qualifying data
        try:
            quali = fastf1.get_session(year, gp_round, "Q")
            quali.load(laps=True, telemetry=False, weather=False, messages=False)

            # For results
            quali_results = quali.results.copy()
            quali_results["RoundNumber"] = gp_round
            quali_results["EventName"] = gp_name
            quali_results["Season"] = year
            all_qualifying.append(quali_results)

            # For lap by lap
            quali_laps = quali.laps.copy()
            quali_laps["RoundNumber"] = gp_round
            quali_laps["EventName"] = gp_name
            quali_laps["Season"] = year
            all_qualifying_laps.append(quali_laps)
        except Exception as e:
            print(f"Qualifying: {e}")

    # saving to csv

    if all_laps:
        laps_df = pd.concat(all_laps, ignore_index=True)
        laps_df.to_csv(f"data/laps/laps_{year}.csv", index=False)

    if all_results:
        results_df = pd.concat(all_results, ignore_index=True)
        results_df.to_csv(f"data/race/race_results_{year}.csv", index=False)

    if all_qualifying:
        quali_df = pd.concat(all_qualifying, ignore_index=True)
        quali_df.to_csv(f"data/qualifying/qualifying_results_{year}.csv", index=False)

    if all_qualifying_laps:
        quali_laps_df = pd.concat(all_qualifying_laps, ignore_index=True)
        quali_laps_df.to_csv(f"data/qualifying_laps/qualifying_laps_{year}.csv", index=False)