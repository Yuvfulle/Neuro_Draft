import time
import json
import requests
import pandas as pd
import concurrent.futures

# only Ranked AP ; AP , SD , RD - types of matches that is not interested
# main question is mmr of each game - count we that or not.
# new patch - 1772088800
# 1774612136 - 215405 = 1774396731

MAX_VALUE_CONST = 9999999999
new_patch_time = 1774396731
main_df = pd.DataFrame(columns=['match_id' , 'radiant_win' , 'avg_rank_tier' , 'radiant_team' , 'dire_team'])
start = time.time()

def get_matches(timeline):
    chunks = []

    counter_requests = 0
    last_match_id = MAX_VALUE_CONST
    last_start_time = MAX_VALUE_CONST
    big_double_red_russian_svo_sword = 0

    bd_data = pd.read_csv("NewMLDotaDB.csv")
    if not bd_data.empty:
        last_match_id = bd_data['match_id'].min()
        last_start_time = timeline + 1
        print("from:" , last_match_id)

    while last_start_time > timeline and counter_requests < 100:
        try:         
            url = "https://api.opendota.com/api/publicMatches"
            r = requests.get(url, params={"less_than_match_id":last_match_id})
            data = r.json()

            if not data:
                last_match_id -= 10
                continue

            df = pd.DataFrame(data)

            last_match_id = df['match_id'].min()
            current_batch_time = df['start_time'].min()
            last_start_time = last_start_time - 10 if pd.isna(current_batch_time) else current_batch_time

            sorted_df = df[(df['game_mode'] == 22) & (df['lobby_type'] == 7)]

            if not sorted_df.empty:
                chunks.append(sorted_df[['match_id','radiant_win','avg_rank_tier','radiant_team','dire_team']])
                big_double_red_russian_svo_sword += len(sorted_df)
                print(big_double_red_russian_svo_sword,f" beetwen -> {last_start_time - timeline}")

            counter_requests += 1
            print(counter_requests)

            time.sleep(1)

        except Exception as e:
            print("request failed:" , e)
            last_match_id -= 50
            time.sleep(2)
            counter_requests += 1
            print(counter_requests)
            continue

    return pd.concat(chunks)

chunks = get_matches(new_patch_time)

data = pd.read_csv("NewMLDotaDB.csv")
data.columns = ['match_id' , 'radiant_win' , 'avg_rank_tier' , 'radiant_team' , 'dire_team']

if not chunks.empty:
    united_df = pd.concat([data , chunks], join='inner' , ignore_index=True)
    chunks_total = united_df.drop_duplicates(subset=['match_id'], keep='first')
    chunks_total.to_csv("NewMLDotaDB.csv", index=False)

    end = time.time()
    print(f"time for {chunks.__len__()} is {end - start}")

else:
    print("empty")