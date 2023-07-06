import warnings
import numbers
from decimal import *
from . import MetricsUtils

class Metrics:
    def __init__(self, supported_funcs):
        self._supported_funcs = supported_funcs

    def __getattribute__(self, name):
        try:
            attr = object.__getattribute__(self, name)
        except:
            attr = eval("MetricsUtils." + name)
        return attr

    def get_supported_funcs(self):
        return self._supported_funcs

    def metrics_dict(self, y_1, y_2, func_li, decimal_points=getcontext().prec):
        metric_d = {}
        sel_func_li = list(set(self._supported_funcs).intersection(set(func_li)))
        if len(sel_func_li) < len(func_li):
            print(func_li)
            warnings.warn("Some or all of the metrics passed are not supported!")

        for func in sel_func_li:
            try:
                value = eval(func)(y_1, y_2)
            except:
                value = eval("MetricsUtils." + func)(y_1, y_2)
            if isinstance(value, numbers.Number):
                metric_d[func] = round(value, decimal_points)
            else:
                metric_d[func] = round(value[0], decimal_points)
        return metric_d


class RegressionMetrics(Metrics):
    def __init__(self, extra_funcs = []):
        supported_funcs = ["max_error", "mean_absolute_error", "median_absolute_error", "mean_squared_log_error",
                           "mean_squared_error", "normalized_root_mean_squared_error_mean_norm",
                           "root_mean_squared_error", "normalized_root_mean_squared_error_range_norm",
                           "mean_absolute_percentage_error", "mean_absolute_percentage_error_average_divisor",
                           "mean_pinball_loss", "r2_score", "explained_variance_score", "mean_tweedie_deviance",
                           "mean_poisson_deviance","mean_gamma_deviance","d2_tweedie_score"]
        supported_funcs.extend(extra_funcs)
        super().__init__(supported_funcs)

    def metrics_dict(self, y_true, y_pred, func_li=[], decimal_points=getcontext().prec):
        if func_li==[]:
            func_li = self.get_supported_funcs()
        return super().metrics_dict(y_true, y_pred, func_li, decimal_points)

class PairwiseMetrics(Metrics):
    def __init__(self, extra_funcs = []):
        supported_funcs = ["kl_divergence", "ks_statistic", "spearmanr", "kendalltau", "pearsonr",
                           "cosine_similarity", "concordance_index"]
        supported_funcs.extend(extra_funcs)
        super().__init__(supported_funcs)

    def metrics_dict(self, y_1, y_2, func_li=[], decimal_points=getcontext().prec):
        if func_li==[]:
            func_li = self.get_supported_funcs()
        return super().metrics_dict(y_1, y_2, func_li, decimal_points)

regression = RegressionMetrics()
pairwise = PairwiseMetrics()

