Overview
========

This project aims at developing supervised-learning models in order to predict game outcomes for the soccer's English Premier League. Please see the presentation slides ``Presentation_SA.pdf`` for further explanations. This repositorty contains code and developement for the machine learning model and the betting strategies, related to slides 4, 5 and 6 of the presentation.


Data
====

Initial data has been collected from https://datahub.io/sports-data/english-premier-league for 7 seasons from 2012-2013 to last year's 2018-2019.
Additionaly, team's market values were webscrapped from https://www.transfermarkt.co.uk/premier-league/marktwerteverein/wettbewerb/GB1
The code relevant to data extraction is in ``data/get_data.py``.

The document ``optimal_ratings.csv`` contains optimal ratings for all teams in each season, resulting from a previous analysis.

The notebook ``notebooks/manipulating_data.ipynb`` includes relevant feature engineering in order to prepare data for future models.


Models
======

Models are developped in the notebook ``notebooks/main_models.ipynb``.
A Random Forest is trained by Cross Validation on the training set (6 first seasons), using diffent sets of features. The best performing model is found to be the Random Forest trained with the complete set of features for both teams (in opposition to the "diff" features only).
