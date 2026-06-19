# #!/usr/bin/env python3
# """
# Quick test script to verify the global filter functions work correctly.
# Run this to test the data loader functions without starting the full dashboard.
# """

# from data_loader import (
#     get_all_seasons,
#     get_circuits_for_season,
#     get_drivers_for_race,
#     get_teams_for_race,
#     load_race_data
# )

# def test_filters():
#     print("🏎️  Testing F1 Dashboard Global Filters")
#     print("=" * 50)
    
#     # Test 1: Get all seasons
#     print("\n1. Testing get_all_seasons():")
#     seasons = get_all_seasons()
#     print(f"   Available seasons: {seasons}")
    
#     if not seasons:
#         print("   ❌ No seasons found! Check if CSV files exist in data/laps/")
#         return
    
#     # Test 2: Get circuits for latest season
#     latest_season = seasons[0]
#     print(f"\n2. Testing get_circuits_for_season({latest_season}):")
#     circuits = get_circuits_for_season(latest_season)
#     print(f"   Found {len(circuits)} circuits:")
#     for circuit in circuits[:5]:  # Show first 5
#         print(f"   - Round {circuit['RoundNumber']}: {circuit['EventName']}")
#     if len(circuits) > 5:
#         print(f"   ... and {len(circuits) - 5} more")
    
#     if not circuits:
#         print(f"   ❌ No circuits found for {latest_season}!")
#         return
    
#     # Test 3: Get drivers for first race
#     first_race = circuits[0]['EventName']
#     print(f"\n3. Testing get_drivers_for_race({latest_season}, '{first_race}'):")
#     drivers = get_drivers_for_race(latest_season, first_race)
#     print(f"   Found {len(drivers)} drivers: {', '.join(drivers)}")
    
#     # Test 4: Get teams for first race
#     print(f"\n4. Testing get_teams_for_race({latest_season}, '{first_race}'):")
#     teams = get_teams_for_race(latest_season, first_race)
#     print(f"   Found {len(teams)} teams:")
#     for team in teams:
#         print(f"   - {team}")
    
#     # Test 5: Load race data
#     print(f"\n5. Testing load_race_data({latest_season}, '{first_race}', 'laps'):")
#     laps_df = load_race_data(latest_season, first_race, 'laps')
#     if not laps_df.empty:
#         print(f"   ✅ Loaded {len(laps_df)} lap records")
#         print(f"   Columns: {list(laps_df.columns)}")
#         print(f"   Total laps: {laps_df['LapNumber'].max()}")
#         print(f"   Drivers in data: {laps_df['Driver'].nunique()}")
#     else:
#         print("   ❌ No lap data loaded!")
    
#     print("\n" + "=" * 50)
#     print("✅ Filter testing complete!")
#     print("\nIf all tests passed, your global filters should work correctly.")
#     print("Start the dashboard with: python main.py")
#     print("Then visit: http://127.0.0.1:8050")

# if __name__ == "__main__":
#     test_filters()