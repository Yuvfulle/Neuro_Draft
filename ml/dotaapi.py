import time
import json
import requests
import pandas as pd
import concurrent.futures

## todo -> mask that return ..._that_pick is not right - in mask that used for save hero id all heros is sorted by id's but first it's located with random -> not ordered.

def make_bit_mask_picked(link):
    hero_bit_mask = 0
    team_bit_mask = 0
    if not isinstance(link , list):
        print('miss match type of link obj')
    else:
        for i in link:
            if i['is_pick'].lower() == 'true':
                hero_bit_mask |= 1<<int(i['hero'])
                if int(i['team'])%2 != 0:
                    team_bit_mask |= 1<<int(i['hero'])
    return [hero_bit_mask , team_bit_mask]

def get_id_matches(T1,step):
    LIMIT = 400
    query = f"""SELECT match_id FROM matches WHERE start_time BETWEEN {T1} AND {T1+step} LIMIT {LIMIT}""" # 1766595291 / 1747958400  {cell:24 624 000} -> 1772582400
    url = f'https://api.opendota.com/api/explorer'
    r = requests.get(url , params={"sql": query})
    data = r.json()

    match_id_list = [row["match_id"] for row in data["rows"]]
    print("count of matches -> "+str(match_id_list.__len__()))
    return match_id_list

def get_json_for_match_list(list):
    
    query_list_of_id = f"""
    SELECT 
        m.match_id,
        m.radiant_win,
        json_agg(
            json_build_object(
                'is_pick' , dt ->> 'pick',
                'team' , dt ->> 'active_team',
                'hero' , dt ->> 'hero_id'
            )
        ) AS draft_list
    FROM matches m
    CROSS JOIN LATERAL unnest(m.draft_timings) AS dt
    WHERE match_id 
    IN ({','.join(map(str,list))})
    GROUP BY m.match_id, m.radiant_win, m.duration;
    """

    url = f'https://api.opendota.com/api/explorer'
    r = requests.get(url , params={"sql":query_list_of_id})
    res = r.json()
    
    return res

#code

start = time.time()

rows = []
step = 246240
for i in range(100):
    print(i)
    match_ids = get_id_matches(1747958400 + i*step , step)
    res = get_json_for_match_list(match_ids)

    for i in res['rows']:
        bit_data = make_bit_mask_picked(i['draft_list'])

        rows.append({
            "match_id": i["match_id"],
            "radiant_win": i["radiant_win"],
            "hero_bit_mask": bit_data[0],
            "team_bit_mask": bit_data[1]
            })
    time.sleep(1)

df = pd.DataFrame(rows)
print(df)
df.to_csv("MLDotaDB.csv")

end = time.time()
print(f"time for {df.__len__()} is {end - start}")

#127 bits pick heros d/r // sorted + 127 bits banned heros b/nb // sorted by id's
#in sorted peaks and bans -> order of ban or peak. -> nums 1-21 +- 
#rank tier for every hero - 1-80
#lane/lane_role for every peak hero in 
#duration
#radiant_win?
#!!! 0 - radiant, 1 - dire -> it's will be another mask and when i make & i take all dire heroes


#in (parsed!?) match from sql get response -> draft_timings -> field to determind is match parsed -> version in parsed match
#think that get any data and safe it after getting in sql database is the best way.