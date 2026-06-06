
import math
from collections import namedtuple

import pandas as pd

from web.services import data_service, model_service

SAMPLE = 100000

Match = namedtuple("Match", "radiant dire rank won")

STAGES = [
    ("0/10", 0, 0), 
    ("1/10", 1, 0), 
    ("4/10", 2, 2),
    ("5/10", 3, 2), 
    ("8/10", 4, 4), 
    ("9/10", 4, 5), 
    ("10/10", 5, 5)
]

def parse_team(value):
    return [int(x.strip()) for x in value.strip("[]").split(",")]


def load_matches(path):
    df = pd.read_csv(path, nrows = SAMPLE)
    return [
        Match(
            radiant = parse_team(row.radiant_team),
            dire = parse_team(row.dire_team),
            rank = int(row.avg_rank_tier),
            won = bool(row.radiant_win),
        )for row in df.itertuples(index=False)
    ]


def avg_winrate(team, rank_group):
    if not team:
        return 50.0
    return sum(data_service.get_winrate(h, rank_group) for h in team) / len(team)


def model_guesses(matches, nr, nd):
    rows = [(m.radiant[:nr], m.dire[:nd]) for m in matches]
    ranks = [m.rank for m in matches]
    return [p > 0.5 for p in model_service.predict_package(rows, ranks)]


def baseline_guesses(matches, nr, nd):
    if nr == 0 and nd == 0:
        return [i % 2 == 0 for i in range(len(matches))]

    out = []
    for m in matches:
        rank_group = data_service.rank_group(m.rank)
        out.append(avg_winrate(m.radiant[:nr], rank_group) > avg_winrate(m.dire[:nd], rank_group))
    return out


def accuracy(guesses, matches):
    correct = [guesses[i] == matches[i].won for i in range(len(matches))]    
    p = sum(correct) / len(correct)
    margin = 1.96 * math.sqrt(p * (1 - p) / len(correct))
    return p, margin


def gap(model_g, base_g, matches):
    diffs = []
    for i in range(len(matches)):
        model_correct = model_g[i] == matches[i].won
        baseline_correct = base_g[i] == matches[i].won
        diffs.append(model_correct - baseline_correct)    
    mean = sum(diffs) / len(diffs)
    var = sum((d - mean) ** 2 for d in diffs) / len(diffs)
    margin = 1.96 * math.sqrt(var / len(diffs))
    return mean, margin


def main():
    matches = load_matches("NewMLDotaDB.csv")
    for label, nr, nd in STAGES:
        model_guessed = model_guesses(matches, nr, nd)
        base_guessed = baseline_guesses(matches, nr, nd)
        model_accuracy, model_error = accuracy(model_guessed, matches)
        base_accuracy, base_error = accuracy(base_guessed, matches)
        difference, difference_error = gap(model_guessed, base_guessed, matches)
        model_col = f"{model_accuracy:.1%} +- {model_error:.1%}"
        base_col = f"{base_accuracy:.1%} +- {base_error:.1%}"
        diff_col = f"{difference:+.1%} +- {difference_error:.1%}"
        print(f"{label}: модель {model_col}, baseline {base_col}, разница {diff_col}")

if __name__ == "__main__":
    main()
