#Copyright (c) Microsoft. All rights reserved.
from tensorflow.keras.layers import (
    Conv1D,
    Input,
    concatenate,
    Dropout,
    BatchNormalization,
    Reshape,
)
from tensorflow.keras.layers import (
    Flatten,
    GRU,
    LSTM,
    TimeDistributed,
    Dense,
    Permute,
    Bidirectional,
)
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow import keras
from numpy.random import seed
#from tensorflow.random import set_seed


def cnn_layers(n_timesteps, n_features, kernel_size=4):
    in1 = Input(
        shape=(
            n_timesteps,
            n_features,
        )
    )
    conv1 = Conv1D(
        2, kernel_size, strides=1, activation="relu", kernel_initializer="he_normal"
    )(in1)
    conv1 = BatchNormalization()(conv1)
    conv2 = Conv1D(
        4, kernel_size, strides=1, activation="relu", kernel_initializer="he_normal"
    )(conv1)
    conv2 = BatchNormalization()(conv2)
    conv3 = Conv1D(
        8, kernel_size, strides=1, activation="relu", kernel_initializer="he_normal"
    )(conv2)
    # conv3 = BatchNormalization()(conv3)
    flat1 = Flatten()(conv3)

    return in1, flat1


def rnn_layer(layer, n_timesteps, n_features, num_layers, d_model, rate):
    in1 = Input(
        shape=(
            n_timesteps,
            n_features,
        )
    )

    # Add extra CNN layer to reduce the number of steps
    if n_timesteps > 10000:
        c1 = Conv1D(
            filters=n_features,
            kernel_size=15,
            strides=15,
            activation="relu",
            kernel_initializer="he_normal",
        )(in1)
        c1 = BatchNormalization()(c1)
    else:
        c1 = in1

    if layer == "lstm":
        encoder = LSTM(units=d_model, return_sequences=True)
    elif layer == "gru":
        encoder = GRU(units=d_model, return_sequences=True)
    elif layer == "bilstm":
        base_rnn = LSTM(units=d_model, return_sequences=True)
        encoder = Bidirectional(base_rnn, merge_mode="concat")
    elif layer == "bigru":
        base_rnn = GRU(units=d_model, return_sequences=True)
        encoder = Bidirectional(base_rnn, merge_mode="concat")

    encoded = encoder(c1)
    if num_layers > 1:
        encoders = [encoder]
    for ii in range(1, num_layers):
        encoder = LSTM(units=d_model, return_sequences=True)
        encoded = encoder(encoded)
        encoders.append(encoder)
    return in1, encoded


def build_multilevel_rnn_unequal(inp_seq_len, inp_features, tgt_seq_len, **kwargs):
    """
    input sequence length does not have to be same as the target
    sequence length; required for short term forecasting where
    window length is greater than the forecast horizon

    """
    tgt_features = kwargs.get("tgt_features", 1)
    rnn = kwargs.get("rnn", "lstm-lstm")
    num_layers = kwargs.get("num_layers", 2)
    d_model = kwargs.get("d_model", 128)
    d_model2 = kwargs.get("d_model2", 16)
    d_model3 = kwargs.get("d_model3", 16)
    # num_heads = kwargs.get("num_heads", 8)
    # dff = kwargs.get("dff", 128)
    seed_value = kwargs.get("seed", 100)
    rate = kwargs.get("rate", 0.1)
    components = kwargs.get("components", 2)
    future_covariates = kwargs.get("future_covariates", False)
    dim_future_cov = kwargs.get("dim_future_cov", 1)
    quantiles = kwargs.get("quantiles", None)

    seed(seed_value)
#    set_seed(seed_value)

    inputs, flat = [], []
    for ii in range(components):
        t_in, t_flat = rnn_layer(
            rnn.split("-")[0], inp_seq_len, inp_features, num_layers, d_model, rate
        )
        inputs.append(t_in)
        flat.append(t_flat)

    if future_covariates:
        decoder_inputs = Input(
            shape=(
                tgt_seq_len,
                dim_future_cov,
            )
        )
        inputs.append(decoder_inputs)

    if components > 1:
        merge = concatenate(flat, axis=-1)  # (b, inp_seq_len, h)
    else:
        merge = flat[0]
    # merge = BatchNormalization()(merge)

    if rnn.split("-")[1] == "lstm":
        encoder2 = LSTM(units=d_model2, activation="relu", return_sequences=True)
    elif rnn.split("-")[1] == "gru":
        encoder2 = GRU(units=d_model2, activation="relu", return_sequences=True)
    elif rnn.split("-")[1] == "bilstm":
        base_rnn = LSTM(units=d_model2, activation="relu", return_sequences=True)
        encoder2 = Bidirectional(base_rnn, merge_mode="concat")
    elif rnn.split("-")[1] == "bigru":
        base_rnn = GRU(units=d_model2, activation="relu", return_sequences=True)
        encoder2 = Bidirectional(base_rnn, merge_mode="concat")

    if future_covariates:
        # Use the context as initial state for the decoder
        # merge = Flatten()(merge)
        # state_h = Dense(d_model2, activation="relu")(merge)
        # state_c = Dense(d_model2, activation="relu")(merge)
        # encoder_states = [state_h, state_c]
        # lstm_out = encoder2(decoder_inputs, initial_state=encoder_states)

        # Directly add the future covariates to the input to the decoder
        merge = Permute((2, 1), input_shape=(inp_seq_len, components * d_model))(merge)
        merge = Dense(tgt_seq_len, activation="relu")(merge)
        merge = Permute((2, 1), input_shape=(components * d_model, tgt_seq_len))(merge)
        merge = concatenate([merge, decoder_inputs], axis=-1)
        lstm_out = encoder2(merge)

    else:
        # convert to the target_sequence_length
        merge = Permute((2, 1), input_shape=(inp_seq_len, components * d_model))(merge)
        merge = Dense(tgt_seq_len, activation="relu")(merge)
        merge = Permute((2, 1), input_shape=(components * d_model, tgt_seq_len))(merge)
        lstm_out = encoder2(merge)

    dense1 = TimeDistributed(Dense(d_model3, activation="relu"))(lstm_out)
    # dropout1 = Dropout(0.2)(dense1)

    if quantiles:
        outputs = []
        for ii in range(quantiles):
            output = TimeDistributed(
                Dense(tgt_features), name="quantile_" + str(ii + 1)
            )(dense1)
            outputs.append(output)

    else:
        outputs = TimeDistributed(Dense(tgt_features))(dense1)

    model = Model(inputs=inputs, outputs=outputs)
    return model
