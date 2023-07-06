#Copyright (c) Microsoft. All rights reserved.
import math
import numpy as np
import pandas as pd
import pickle
import pywt
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm


def get_wavelet_reconstruction(x, wavelet="db5", levels=5, col_indices=[]):
    """
    x: window data, dimension: window length X number of features
    wavelet: wavelet name
    levels: number of levels in the wavelet transform
    col_indices: index of the columns for which wavelet transform is desired
    """
    N, ncol = x.shape
    xout = [np.zeros(x.shape) for _ in range(levels)]
    for icol in range(ncol):
        if icol in col_indices:
            wp5 = pywt.wavedec(
                data=x[:, icol], wavelet=wavelet, mode="symmetric", level=levels
            )
            for i in range(1, levels + 1):
                xout[i - 1][:, icol] = pywt.waverec(wp5[:-i] + [None] * i, wavelet)[:N]
        else:
            for i in range(1, levels + 1):
                xout[i - 1][:, icol] = x[:, icol]

    return xout


def dl_preprocess_data(
    df,
    ts_lookback,
    ts_lookahead,
    pred_vars,
    per_split=0.80,
    levels=5,
    wv_cols=None,
    future_cols=None,
    shift_label=0,
    step_label=1,
    step_input=1,
    split_date=None,
    scale_output=True,
    scale_output_class=None,
    scale_input_class=None,
):

    if split_date:
        if ":" not in split_date:
            split_date += " 00:00:00"
        df.insert(0, "row_num", range(0, len(df)))
        idx = df.index[df.index == split_date]
        split_index = df.loc[idx]["row_num"][0]
        df.drop(columns=["row_num"], inplace=True)

    n_in = ts_lookback
    if scale_input_class is None:
        scaler = StandardScaler()
    else:
        scaler = scale_input_class

    scaled_df = scaler.fit_transform(df)
    scaled_df = pd.DataFrame(scaled_df, columns=df.columns, index=df.index)

    # column indices on which wavelet transformation will be done
    wv_indices = []
    columns = list(scaled_df.columns)
    if wv_cols:
        for w in wv_cols:
            wv_indices.append(columns.index(w))
    else:
        wv_indices = list(range(len(columns)))

    future_indices = []
    if future_cols:
        for f in future_cols:
            future_indices.append(columns.index(f))

    data = scaled_df.values.astype(float)

    n_out = ts_lookahead
    label_df = df.copy()
    for column in label_df:
        if column not in pred_vars:
            label_df.drop(columns=column, inplace=True)
    label_df = label_df[pred_vars]  # keep the orders

    if scale_output is True:
        if scale_output_class is None:
            scaler_y = StandardScaler()
        else:
            scaler_y = scale_output_class
        label_data = scaler_y.fit_transform(label_df)

    else:
        scaler_y = None
        label_data = label_df.to_numpy()

    scaled_label_df = pd.DataFrame(
        label_data, index=label_df.index, columns=label_df.columns
    )

    # label_data = label_df.values
    X, y = [list() for _ in range(levels + 1)], list()

    if future_cols:
        X_f = list()

    in_start = 0
    # step over the entire history one time step at a time
    # reshape input to be 3D [samples, timesteps, features]
    for _ in tqdm(range(len(data))):
        # define the end of the input sequence
        in_end = in_start + n_in
        out_end = in_end + n_out + shift_label

        # ensure we have enough data for this instance
        if out_end < len(data):
            x0 = data[in_start:in_end, :]
            X[0].append(x0)
            if levels > 0:
                xwv = get_wavelet_reconstruction(
                    x0, levels=levels, col_indices=wv_indices
                )
                for ii in range(levels):
                    X[ii + 1].append(xwv[ii])

            # this one will take the raw value - high frequency
            # y.append(label_data[in_end + shift_label : out_end : step_label, :])

            # this one will take the average value
            # y.append(scaled_label_df[in_end + shift_label : out_end].groupby(pd.Grouper(freq='15min')).mean().values)

            # explicit averaging over the next 15 steps
            y_ = []
            for ii in range(in_end + shift_label, out_end, step_label):
                # print(label_data[ii : ii + step_label, :])
                y__ = label_data[ii : ii + step_label, :].mean(axis=0)
                # if len(pred_vars) == 1:
                #     y_.append([y__])
                # else:
                y_.append(y__)

            y.append(y_)

            # collect future covariates - no wavelet transformation
            if future_cols:
                X_f.append(
                    data[in_end + shift_label : out_end : step_label, future_indices]
                )

        # move along one time step
        in_start += step_input

    X = [np.array(x_ii) for x_ii in X]
    y = np.array(y)
    if future_cols:
        X_f = np.array(X_f)

    if not split_date:
        split_index = math.ceil(len(y) * per_split)

    train_X, train_y = [x_ii[:split_index, :, :] for x_ii in X], y[:split_index, :, :]
    test_X, test_y = [x_ii[split_index:, :] for x_ii in X], y[split_index:, :]

    if future_cols:
        future_train_X, future_test_X = X_f[:split_index, :, :], X_f[split_index:, :, :]
        train_X.append(future_train_X)
        test_X.append(future_test_X)
    return scaler, scaler_y, train_X, train_y, test_X, test_y, split_index


def convert_df_wavelet_input(
    data_df,
    n_pred_var=["Radiation"],
    wb=True,
    ts_lookback=24,
    ts_lookahead=24,
    per_split=0.90,
    levels=5,
    wv_cols=None,
    future_cols=None,
    shift_label=0,
    step_label=1,
    step_input=1,
    split_date=None,
):

    split_index = None
    (
        scaler,
        scaler_y,
        train_X,
        train_y,
        test_X,
        test_y,
        split_index,
    ) = dl_preprocess_data(
        data_df,
        ts_lookback=ts_lookback,
        ts_lookahead=ts_lookahead,
        pred_vars=n_pred_var,
        per_split=per_split,
        levels=levels,
        wv_cols=wv_cols,
        future_cols=future_cols,
        shift_label=shift_label,
        step_label=step_label,
        step_input=step_input,
        split_date=split_date,
    )

    if wb is True:
        with open(
            "serialized/radiation_output_normalization_class", "wb"
        ) as scaler_y_file:
            pickle.dump(scaler_y, scaler_y_file)

        with open(
            "serialized/radiation_input_normalization_class", "wb"
        ) as scaler_X_file:
            pickle.dump(scaler, scaler_X_file)

    return scaler, scaler_y, train_X, train_y, test_X, test_y, split_index


def dl_preprocess_data_test(
    df,
    ts_lookback,
    ts_lookahead,
    pred_vars,
    scale_output=True,
    levels=5,
    wv_cols=None,
    future_cols=None,
    shift_label=0,
    step_label=1,
    step_input=1,
    scale_output_class=None,
    scale_input_class=None,
):

    n_in = ts_lookback
    n_out = ts_lookahead

    if scale_input_class is None:
        raise ValueError("Scale class cannot be None")
    else:
        scaler = scale_input_class

    scaled_df = scaler.transform(df)  # only transform
    scaled_df = pd.DataFrame(scaled_df, columns=df.columns, index=df.index)

    # column indices on which wavelet transformation will be done
    wv_indices = []
    columns = list(scaled_df.columns)
    if wv_cols:
        for w in wv_cols:
            wv_indices.append(columns.index(w))
    else:
        wv_indices = list(range(len(columns)))

    future_indices = []
    if future_cols:
        for f in future_cols:
            future_indices.append(columns.index(f))

    data = scaled_df.values.astype(float)

    label_df = df.copy()
    for column in label_df:
        if column not in pred_vars:
            label_df.drop(columns=column, inplace=True)
    label_df = label_df[pred_vars]

    if scale_output is True:
        if scale_output_class is None:
            raise ValueError("Scale class cannot be None")
        else:
            scaler_y = scale_output_class
        label_data = scaler_y.transform(label_df)  # only transform
    else:
        scaler_y = None
        label_data = label_df.to_numpy()

    scaled_label_df = pd.DataFrame(
        label_data, index=label_df.index, columns=label_df.columns
    )
    X, y = [list() for _ in range(levels + 1)], list()
    if future_cols:
        X_f = list()

    in_start = 0
    # step over the entire history one time step at a time
    # reshape input to be 3D [samples, timesteps, features]
    for _ in tqdm(range(len(data))):
        # define the end of the input sequence
        in_end = in_start + n_in
        out_end = in_end + n_out + shift_label
        # ensure we have enough data for this instance
        if out_end < len(data):
            x0 = data[in_start:in_end, :]
            X[0].append(x0)

            if levels > 0:
                xwv = get_wavelet_reconstruction(
                    x0, levels=levels, col_indices=wv_indices
                )
                for ii in range(levels):
                    X[ii + 1].append(xwv[ii])

            # this one will take the raw value - high frequency
            # y.append(label_data[in_end + shift_label : out_end : step_label, :])
            # print(scaled_label_df[in_end + shift_label : out_end])
            # print(scaled_label_df[in_end + shift_label : out_end].groupby(pd.Grouper(freq='15min')).mean())
            # print(scaled_label_df[in_end + shift_label : out_end].rolling(window=15).mean())
            # print(scaled_label_df[in_end + shift_label : out_end].groupby(pd.Grouper(freq='15min')).mean().values[-6:])

            # explicit averaging
            y_ = []
            for ii in range(in_end + shift_label, out_end, step_label):
                y__ = label_data[ii : ii + step_label].mean(axis=0)
                y_.append(y__)
                # y_.append([y__])

            y.append(y_)

            # this one will take the average value
            # y.append(scaled_label_df[in_end + shift_label : out_end].groupby(pd.Grouper(freq='15min')).mean().values[-6:])

            # collect future covariates
            if future_cols:
                X_f.append(
                    data[in_end + shift_label : out_end : step_label, future_indices]
                )

        # move along one time step
        in_start += step_input

    X = [np.array(x_ii) for x_ii in X]
    y = np.array(y)
    if future_cols:
        X_f = np.array(X_f)
        X.append(X_f)

    return X, y


def prepare_multiscale_input(
    df,
    n_pred_var="Radiation",
    wb=True,
    ts_lookback=24,
    ts_lookahead=24,
    per_split=0.90,
    shift_label=0,
    step_label=1,
    step_input=1,
    split_date=None,
    validation=True,
    scale_output=True,
    scale_output_class=None,
    scale_input_class=None,
    reverse_input=True,
):

    pred_var_idx = [n_pred_var]

    if split_date:
        if ":" not in split_date:
            split_date += " 00:00:00"
        df.insert(0, "row_num", range(0, len(df)))
        idx = df.index[df.index == split_date]
        split_index = df.loc[idx]["row_num"][0]
        df.drop(columns=["row_num"], inplace=True)

    n_in = ts_lookback
    if scale_input_class is None:
        scaler = StandardScaler()
    else:
        scaler = scale_input_class

    scaled_df = scaler.fit_transform(df)
    scaled_df = pd.DataFrame(scaled_df, columns=df.columns, index=df.index)

    data = scaled_df.values.astype(float)

    n_out = ts_lookahead
    label_df = df.copy()
    for column in label_df:
        if column not in pred_var_idx:
            label_df.drop(columns=column, inplace=True)

    if scale_output is True:
        if scale_output_class is None:
            scaler_y = StandardScaler()
        else:
            scaler_y = scale_output_class
        label_data = scaler_y.fit_transform(label_df)

    else:
        scaler_y = None
        label_data = label_df.to_numpy()

    scaled_label_df = pd.DataFrame(
        label_data, index=label_df.index, columns=label_df.columns
    )

    if wb is True:
        with open(
            "serialized/radiation_output_normalization_class", "wb"
        ) as scaler_y_file:
            pickle.dump(scaler_y, scaler_y_file)

        with open(
            "serialized/radiation_input_normalization_class", "wb"
        ) as scaler_X_file:
            pickle.dump(scaler, scaler_X_file)

    # label_data = label_df.values
    X, y = [list() for _ in range(4)], list()
    in_start = 0
    # step over the entire history one time step at a time
    # reshape input to be 3D [samples, timesteps, features]
    for _ in tqdm(range(len(data))):
        # define the end of the input sequence
        in_end = in_start + n_in
        out_end = in_end + n_out + shift_label
        # ensure we have enough data for this instance
        if out_end < len(data):
            x_15 = (
                scaled_df[in_start:in_end]
                .groupby(pd.Grouper(freq="15min"))
                .mean()
                .values
            )
            N = x_15.shape[0]
            x0 = data[in_end - N : in_end, :]
            x2 = (
                scaled_df[in_start:in_end]
                .groupby(pd.Grouper(freq="10min"))
                .mean()
                .values[-N:]
            )
            x3 = (
                scaled_df[in_start:in_end]
                .groupby(pd.Grouper(freq="5min"))
                .mean()
                .values[-N:]
            )
            # print(x0.shape, x_15.shape, x2.shape, x3.shape)
            # sys.exit()
            if reverse_input:
                X[0].append(np.flipud(x0))
                X[1].append(np.flipud(x3))
                X[2].append(np.flipud(x2))
                X[3].append(np.flipud(x_15))
            else:
                X[0].append(x0)
                X[1].append(x3)
                X[2].append(x2)
                X[3].append(x_15)

            # this one will take the raw value - high frequency
            # y.append(label_data[in_end + shift_label : out_end : step_label, :])

            # this one will take the average value
            # y.append(scaled_label_df[in_end + shift_label : out_end].groupby(pd.Grouper(freq='15min')).mean().values)

            # explicit averaging over the next 15 steps
            y_ = []
            for ii in range(in_end + shift_label, out_end, step_label):
                y__ = label_data[ii : ii + step_label].mean()
                y_.append([y__])

            y.append(y_)

        # move along one time step
        in_start += step_input

    X = [np.array(x_ii) for x_ii in X]
    y = np.array(y)

    if validation is True:
        if not split_date:
            split_index = math.ceil(len(y) * per_split)

        train_X, train_y = [x_ii[:split_index, :, :] for x_ii in X], y[
            :split_index, :, :
        ]
        test_X, test_y = [x_ii[split_index:, :] for x_ii in X], y[split_index:, :]

        return scaler, scaler_y, train_X, train_y, test_X, test_y, split_index
    else:
        return scaler, scaler_y, X, y, None, None, None


def prepare_multiscale_input_test(
    df,
    ts_lookback,
    ts_lookahead,
    pred_var_idx,
    scale_output=True,
    shift_label=0,
    step_label=1,
    step_input=1,
    scale_output_class=None,
    scale_input_class=None,
    reverse_input=True,
):

    n_in = ts_lookback
    if scale_input_class is None:
        raise ValueError("Scale class cannot be None")
    else:
        scaler = scale_input_class

    scaled_df = scaler.transform(df)  # only transform
    scaled_df = pd.DataFrame(scaled_df, columns=df.columns, index=df.index)

    data = scaled_df.values.astype(float)

    n_out = ts_lookahead
    label_df = df.copy()
    for column in label_df:
        if column not in pred_var_idx:
            label_df.drop(columns=column, inplace=True)

    if scale_output is True:
        if scale_output_class is None:
            raise ValueError("Scale class cannot be None")
        else:
            scaler_y = scale_output_class
        label_data = scaler_y.transform(label_df)  # only transform
    else:
        scaler_y = None
        label_data = label_df.to_numpy()

    scaled_label_df = pd.DataFrame(
        label_data, index=label_df.index, columns=label_df.columns
    )
    X, y = [list() for _ in range(4)], list()
    in_start = 0
    # step over the entire history one time step at a time
    # reshape input to be 3D [samples, timesteps, features]
    for _ in tqdm(range(len(data))):
        # define the end of the input sequence
        in_end = in_start + n_in
        out_end = in_end + n_out + shift_label
        # ensure we have enough data for this instance
        if out_end < len(data):
            N = 96  # x_15.shape[0]
            x_15 = (
                scaled_df[in_start:in_end]
                .groupby(pd.Grouper(freq="15min"))
                .mean()
                .values[-96:]
            )
            x0 = data[in_end - N : in_end, :]  # original data, 1 minute interval
            x2 = (
                scaled_df[in_start:in_end]
                .groupby(pd.Grouper(freq="10min"))
                .mean()
                .values[-N:]
            )
            x3 = (
                scaled_df[in_start:in_end]
                .groupby(pd.Grouper(freq="5min"))
                .mean()
                .values[-N:]
            )
            # print(x0.shape, x_15.shape, x2.shape, x3.shape)
            if reverse_input:
                X[0].append(np.flipud(x0))
                X[1].append(np.flipud(x3))
                X[2].append(np.flipud(x2))
                X[3].append(np.flipud(x_15))
            else:
                X[0].append(x0)
                X[1].append(x3)
                X[2].append(x2)
                X[3].append(x_15)

            # this one will take the raw value - high frequency
            # y.append(label_data[in_end + shift_label : out_end : step_label, :])

            # explicit averaging
            y_ = []
            for ii in range(in_end + shift_label, out_end, step_label):
                y__ = label_data[ii : ii + step_label].mean()
                y_.append([y__])

            y.append(y_)

            # this one will take the average value
            # y.append(scaled_label_df[in_end + shift_label : out_end].groupby(pd.Grouper(freq='15min')).mean().values[-6:])
        # move along one time step
        in_start += step_input

    X = [np.array(x_ii) for x_ii in X]
    y = np.array(y)
    return X, y


def rmse(y_true, y_pred):
    return np.sqrt(np.mean((y_pred - y_true) ** 2))


def nrmse2(y_true, y_pred):
    return rmse(y_true, y_pred) / (np.max(y_true) - np.min(y_true))


def mae(y_true, y_pred):
    return np.mean(np.abs(y_pred - y_true))


def nrmse(y_true, y_pred):
    mu = np.mean(y_true)
    if mu != 0:
        return np.sqrt(np.mean((y_pred - y_true) ** 2)) / mu
    else:
        return 0


def mape(y_true, y_pred):
    y_true = y_true.copy()
    y_pred = y_pred.copy()

    # lightgbm style
    y_true[y_true == 0] = 1
    y_pred[y_pred == 0] = 1
    y_true, y_pred = np.array(y_true), np.array(y_pred)

    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def func_mase(training_series, testing_series, prediction_series):
    """
    Computes the MEAN-ABSOLUTE SCALED ERROR forcast error for univariate time series prediction.

    See "Another look at measures of forecast accuracy", Rob J Hyndman

    parameters:
        training_series: the series used to train the model, 1d numpy array
        testing_series: the test series to predict, 1d numpy array or float
        prediction_series: the prediction of testing_series, 1d numpy array (same size as testing_series) or float
        absolute: "squares" to use sum of squares and root the result, "absolute" to use absolute values.

    """
    n = training_series.shape[0]
    d = np.abs(np.diff(training_series)).sum() / (n - 1)

    errors = np.abs(testing_series - prediction_series)
    return errors.mean() / d
