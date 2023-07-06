from . import metrics
from collections import Counter
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from . import  MetricsUtils

class VirtualSensor(ABC):
    def __init__(self, df, colocation_dict, **kwargs):
        self.df = df.copy()
        self.colocation_dict = colocation_dict
        self.params = kwargs

    @abstractmethod
    def _evaluate_sensor_quality(self, dfn, sensor_col_li, reference_col=None):
        raise NotImplementedError("Method not implemented.")

    @abstractmethod
    def _apply_sensor_transformation(self, dfn, sensor_quality_response):
        raise NotImplementedError("Method not implemented.")

    #helper method to get values filled based on availability of sensor order
    def _impute_ws(self, row, sensor_order):
        val = []
        for col in sensor_order:
            val = row[col]
            if np.isnan(val):
                val = None
                col = None
                continue
            else:
                break
        return val, col

    def get_virtual_sensors(self):
        final_dict = {}
        for reference_sensor_col, sensor_col_li in self.colocation_dict.items():
            dfn = self.df.copy()
            if reference_sensor_col not in dfn.columns:
                reference_sensor_col=None
            sensor_quality_response = self._evaluate_sensor_quality(dfn, sensor_col_li, reference_sensor_col)
            dfn[[f'{reference_sensor_col}_virtual', f'{reference_sensor_col}_sensor_tag']] = self._apply_sensor_transformation(dfn, sensor_quality_response)
            final_dict[f'{reference_sensor_col}_virtual'] = dfn
        return final_dict


class KLDivergenceOrder(VirtualSensor):
    def __init__(self, df, colocation_dict, **kwargs):
        super().__init__(df, colocation_dict, **kwargs)
        self.runs = self.params.get('runs', 20)

    def _evaluate_sensor_quality(self, dfn, sensor_col_li, reference_sensor_col):
        sensor_orders = []
        for _ in range(self.runs):
            kl_dict = {}
            for sensor_col in sensor_col_li:
                kl_df = dfn[[sensor_col, reference_sensor_col]]
                kl_df = kl_df.dropna()
                kl_dict[sensor_col] = MetricsUtils.kl_divergence(kl_df[sensor_col], kl_df[reference_sensor_col])
            sensor_list = sorted(kl_dict.items(), key=lambda kv: (kv[1], kv[0]))
            sensor_order = [sensor[0] for sensor in sensor_list]
            sensor_orders.append(sensor_order)
        most_frequent_sensor_order = [list(el) for el, freq in Counter(map(tuple, sensor_orders)).most_common(1)][0]
        return most_frequent_sensor_order

    def _apply_sensor_transformation(self, dfn, sensor_order):
        return dfn.apply(lambda row: self._impute_ws(row, sensor_order), result_type='expand', axis=1)


class PowerCurveOrder(VirtualSensor):
    def __init__(self, df, colocation_dict, **kwargs):
        super().__init__(df, colocation_dict, **kwargs)
        self.power_curve_func = self.params['power_curve_func']

    def _evaluate_sensor_quality(self, dfn, sensor_col_li, reference_sensor_col=None):
        power_dict = {}
        for sensor_col in sensor_col_li:
            power_df = power_df.dropna()
            power_dict[sensor_col] = metrics.root_mean_squared_error(self.power_curve_func(power_df[sensor_col]))
        sensor_list = sorted(power_dict.items(), key=lambda pc: (pc[1], pc[0]))
        sensor_order = [sensor[0] for sensor in sensor_list]
        return sensor_order

    def _apply_sensor_transformation(self, dfn, sensor_order):
        return dfn.apply(lambda row: self._impute_ws(row, sensor_order), result_type='expand', axis=1)


if __name__ == '__main__':
    df = pd.DataFrame({'wind_reference':np.random.normal(0,5,1000), 'wind_sensor_1':np.random.normal(2,5,1000),
                       'wind_sensor_2':np.random.normal(-3,5,1000), 'wind_sensor_3':np.random.normal(1,5,1000)})
    df['wind_sensor_2'][1:800] = np.NaN
    df['wind_sensor_3'][600:] = np.NaN
    colocation_dict = {'wind_reference':['wind_sensor_1','wind_sensor_2', 'wind_sensor_3']}

    params = {'runs':20}
    vs = KLDivergenceOrder(df, colocation_dict, runs=20)
    d = vs.get_virtual_sensors()#get_virtual_sensors(df, colocation_dict)
    print(d['wind_reference'][['wind_reference_virtual','wind_reference_sensor_tag']])#['wind_reference_sensor_tag'].value_counts())

    params = {'entity_col':'Power'}


    """
    
    def get_virtual_sensors(self):
        final_dict = {}
        for reference_sensor_col, sensor_col_li in self.colocation_dict.items():
            dfn = self.df.copy()
            all_cols = sensor_col_li + [reference_sensor_col]
            dfn = dfn[all_cols]
            #sensor_order = get_sensor_order(dfn, reference_sensor_col, sensor_col_li)
            sensor_quality_response = self.evaluate_sensor_quality(dfn, reference_sensor_col, sensor_col_li)
            #dfn[[f'{reference_sensor_col}_virtual', f'{reference_sensor_col}_sensor_tag']] = dfn.apply(
            #    lambda row: self._impute_ws(row, sensor_order), result_type='expand', axis=1)
            dfn[[f'{reference_sensor_col}_virtual', f'{reference_sensor_col}_sensor_tag']] = self.apply_sensor_transformation(dfn, sensor_quality_response)
            final_dict[reference_sensor_col] = dfn
        return final_dict
    """