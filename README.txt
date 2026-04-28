This is a machine learning project that predicts the result of Dota 2 matches based on team drafts. The latest version of the model reached 65.7% accuracy and improved probability calibration, which makes predictions more stable and closer to real win chances.

The model analyzes two teams: Radiant and Dire, and predicts the probability that Radiant will win. The input data includes picked heroes, how heroes work together inside each team, and how heroes counter each other between teams. It also uses match rank level, which is grouped into simple categories (low, mid, high, etc.), so the model can understand differences in skill level.

The main part of the model is feature engineering. For each match, we create features for hero picks, hero pairs inside the same team, and matchups between Radiant and Dire heroes. This helps the model learn both team synergy and counter-picks between heroes.

To improve learning, we use data mirroring. Each match is duplicated with Radiant and Dire swapped, and the result is also flipped. This removes bias toward one side and doubles the dataset size, which helps the model generalize better.

The model uses gradient boosting on decision - LightGBM and XGboost, with GPU support. It is trained with regularization, limited tree depth, and feature sampling. This helps reduce overfitting and makes results more stable.

We also use probability calibration to make predicted probabilities more accurate. This is important because raw boosting models can be overconfident. Calibration improves logloss and makes probability outputs more realistic and easier to interpret.

During training, the data is split into training and test sets in a balanced way to keep class distribution the same. After training, we evaluate the model using accuracy and logloss. We also save all important files, including the model, vectorizer, and matchup statistics.

In the future, the model can be improved by using better hero representations, embeddings, and combining multiple models into an ensemble to get higher accuracy and better predictions.
