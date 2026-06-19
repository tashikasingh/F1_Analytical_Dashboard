import pandas as pd
import os
import fastf1
import fastf1.plotting

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# ======================================================
# HELPERS
# ======================================================
def load_csv(subfolder, filename):
    path = os.path.join(DATA_DIR, subfolder, filename)
    try:
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return pd.DataFrame()


def list_csv_files(subfolder):
    folder = os.path.join(DATA_DIR, subfolder)
    if not os.path.isdir(folder):
        print(f"Folder not found: {folder}")
        return []
    return [f for f in os.listdir(folder) if f.endswith(".csv")]


def load_all(subfolder):
    files = list_csv_files(subfolder)
    dfs = [load_csv(subfolder, f) for f in files]
    dfs = [df for df in dfs if not df.empty]

    if dfs:
        return pd.concat(dfs, ignore_index=True)

    return pd.DataFrame()


# ======================================================
# LOAD DATA
# ======================================================
race_df = load_all("laps")
quali_laps_df = load_all("qualifying_laps")
quali_df = load_all("qualifying_results")
results_df = load_all("race")


# ======================================================
# CLEAN TYPES
# ======================================================
for df in [race_df, quali_laps_df, quali_df, results_df]:
    if not df.empty and "Season" in df.columns:
        df["Season"] = pd.to_numeric(df["Season"], errors="coerce")


# ======================================================
# SEASONS
# ======================================================
seasons = []

if not race_df.empty and "Season" in race_df.columns:
    seasons = sorted(race_df["Season"].dropna().astype(int).unique(), reverse=True)


# ======================================================
# FILTER FUNCTIONS
# ======================================================
def filter_laps(season, race, session):

    if not season or not race:
        return pd.DataFrame()

    df = race_df if session == "Race" else quali_laps_df

    if df.empty:
        return pd.DataFrame()

    return df[
        (df["Season"] == int(season)) &
        (df["EventName"] == race)
    ].copy()


def filter_results(season, race):

    if results_df.empty:
        return pd.DataFrame()

    return results_df[
        (results_df["Season"] == int(season)) &
        (results_df["EventName"] == race)
    ].copy()


def get_races(season, session):

    df = race_df if session == "Race" else quali_df

    if df.empty:
        return []

    temp = df[df["Season"] == int(season)].copy()

    if "RoundNumber" in temp.columns:
        temp = temp.sort_values("RoundNumber")

    return temp["EventName"].dropna().unique().tolist()


# ======================================================
# COLOR MAP
# ======================================================
def get_color_map(season, race, session_type):

    try:
        code = "R" if session_type == "Race" else "Q"

        session = fastf1.get_session(int(season), race, code)
        session.load(laps=False, telemetry=False, weather=False)

        cmap = {}

        for drv in session.drivers:
            try:
                abbr = session.get_driver(drv)["Abbreviation"]
                cmap[abbr] = fastf1.plotting.get_driver_color(
                    abbr, session=session
                )
            except:
                pass

        return cmap

    except Exception as e:
        print("Color map error:", e)
        return {}