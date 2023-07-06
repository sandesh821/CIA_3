import numpy as np
from math import sqrt

#Regression metrics
from sklearn.metrics import *

#pairwise metrics
from sklearn.metrics.pairwise import *
from scipy.spatial.distance import cosine
from scipy.stats import kendalltau, pearsonr
from . import vector2distribution as v2d
kl_divergence = v2d.kl_divergence
ks_statistic = v2d.ks_statistic
cosine_similarity = cosine

#Custom functions can be added here

def root_mean_squared_error(y_true, y_pred):
    return sqrt(mean_squared_error(y_true, y_pred))

def mean_absolute_percentage_error_average_divisor(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / np.mean(y_true))) * 100

def normalized_root_mean_squared_error_mean_norm(y_true, y_pred):
    return sqrt(mean_squared_error(y_true, y_pred))/ np.mean(y_true)

def normalized_root_mean_squared_error_range_norm(y_true, y_pred):
    return sqrt(mean_squared_error(y_true, y_pred))/ (np.max(y_true) - np.min(y_true))