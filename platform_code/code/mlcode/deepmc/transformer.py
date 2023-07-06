#Copyright (c) Microsoft. All rights reserved.
from deepmc.transformer_models_ts import Encoder, FFT
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
    LSTM,
    RepeatVector,
    TimeDistributed,
    Dense,
    Permute,
)
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping
import tensorflow as tf
from tensorflow import keras
from numpy.random import seed
from deepmc.rnn import rnn_layer


class GLU(keras.layers.Layer):
    def __init__(self, units=32):
        super(GLU, self).__init__()
        self.layer1 = Dense(units=units, activation="sigmoid")
        self.layer2 = Dense(units=units, activation="linear")

    def call(self, inputs):
        y1 = self.layer1(inputs)
        y2 = self.layer2(inputs)
        return tf.keras.layers.Multiply()([y1, y2])


class GRN(keras.layers.Layer):
    def __init__(self, units=None):
        super(GRN, self).__init__()
        self.glu = GLU(units)
        self.layer1 = Dense(units=units, activation="linear")
        self.layer2 = Dense(units=units, activation="linear", use_bias=False)
        self.layer3 = Dense(units=units, activation="linear")
        self.layernorm = tf.keras.layers.LayerNormalization(axis=1)

    def call(self, a, c=None):
        x1 = self.layer1(a)
        if c:
            x1 = x1 + self.layer2(c)
        eta2 = keras.activations.elu(x1, alpha=1.0)
        eta1 = self.layer3(eta2)
        return self.layernorm(a + self.glu(eta1))


def deepmc_transformer_layer(
    n_timesteps, n_features, num_layers, d_model, num_heads, dff, pe_input, rate):
    
    in1 = Input(
        shape=(
            n_timesteps,
            n_features,
        )
    )
    
    permin1 = Permute((2,1))(in1)
    encoder = Encoder(num_layers, d_model, num_heads, dff, pe_input, rate)
    encoded = encoder(permin1, True, None)
    # flat1 = Flatten()(encoded)
    return in1, encoded    


    
def transformer_layer(
    n_timesteps, n_features, num_layers, d_model, num_heads, dff, pe_input, rate
):
    in1 = Input(
        shape=(
            n_timesteps,
            n_features,
        )
    )
    encoder = Encoder(num_layers, d_model, num_heads, dff, pe_input, rate)
    encoded = encoder(in1, True, None)
    # flat1 = Flatten()(encoded)
    return in1, encoded

def hidden_transformer_layer(
    layer, num_layers, d_model, num_heads, dff, pe_input, rate
):
    encoder = Encoder(num_layers, d_model, num_heads, dff, pe_input, rate)
    encoded = encoder(layer, True, None)
    # flat1 = Flatten()(encoded)
    return encoded

def build_deepmc_multilevel_transformer(train_X, train_y):
    """
    the input sequence length is same as the output sequence length
    """
    n_outputs = train_y.shape[1]
    num_layers=2
    d_model=48
    num_heads=4
    dff=28
    rate=0.1
            
    inputs, flat = [], []
    components = len(train_X)
    for k in range(components):
        t_in, t_flat = transformer_layer(
            n_timesteps=train_X[k].shape[1],
            n_features = train_X[k].shape[2],
            num_layers=num_layers,
            d_model=d_model,
            num_heads=num_heads,
            dff=dff,
            pe_input=train_X[k].shape[1],
            rate=rate,
        )
        inputs.append(t_in)
        flat.append(t_flat)

    if components > 1:
        merge = concatenate(flat, axis=-1)  # (b, inp_seq_len, h)
    else:
        merge = flat[0]
        
    perm = Permute((2,1))(merge)
    tfmr = hidden_transformer_layer(perm, num_layers, d_model, num_heads, dff, perm.shape[1], rate)
    
    lstm1 = LSTM(n_outputs, activation="relu", return_sequences=True)(tfmr)
    perm2 = Permute((2,1))(lstm1)
    lstm_out = LSTM(16, activation="tanh", return_sequences=True)(perm2)
    dense1 = TimeDistributed(Dense(16, activation="relu"))(lstm_out)
    # dropout1 = Dropout(0.2)(dense1)
    output = TimeDistributed(Dense(1))(dense1)

    model = Model(inputs=inputs, outputs=output)
    model.compile(loss='mse', optimizer='adam')
    return model

def build_deepmc_multilevel_transformer_1out(train_X, train_y):
    """
    the input sequence length is same as the output sequence length
    """
    n_outputs = train_y.shape[1]
    num_layers=2
    d_model=16
    num_heads=4
    dff=28
    rate=0.1
            
    inputs, flat = [], []
    components = len(train_X)
    for k in range(components):
        t_in, t_flat = transformer_layer(
            n_timesteps=train_X[k].shape[1],
            n_features = train_X[k].shape[2],
            num_layers=num_layers,
            d_model=d_model,
            num_heads=num_heads,
            dff=dff,
            pe_input=train_X[k].shape[1],
            rate=rate,
        )
        inputs.append(t_in)
        flat.append(t_flat)

    if components > 1:
        merge = concatenate(flat, axis=-1)  # (b, inp_seq_len, h)
    else:
        merge = flat[0]
        
    perm = Permute((2,1))(merge)
    tfmr = hidden_transformer_layer(perm, num_layers, d_model, num_heads, dff, perm.shape[1], rate)
    perm2 = Permute((2,1))(tfmr)    
    
    flat2 = Flatten()(perm2)
    repeat1 = RepeatVector(n_outputs)(flat2)
    lstm2 = LSTM(8, activation='tanh', return_sequences=True)(repeat1)
    dense1 = TimeDistributed(Dense(16, activation='relu'))(lstm2)
    #dropout1 = Dropout(0.2)(dense1)
    output = TimeDistributed(Dense(1))(dense1)

    model = Model(inputs=inputs, outputs=output)
    model.compile(loss='mse', optimizer='adam')
    return model


def build_multilevel_transformer(train_X, train_y):
    """
    the input sequence length is same as the output sequence length
    """

    n_outputs = train_y.shape[1]
    num_layers=2
    d_model=16
    num_heads=4
    dff=28
    rate=0.1

    #     n_outputs = train_y.shape[1]
    #     _, inp_seq_len, inp_features = train_X[0].shape
    #seed(seed_value)
#    set_seed(seed_value)

    inputs, flat = [], []
    components = len(train_X)

    for k in range(components):
        t_in, t_flat = transformer_layer(
            train_X[k].shape[1],
            n_features = train_X[k].shape[2],
            num_layers=num_layers,
            d_model=d_model,
            num_heads=num_heads,
            dff=dff,
            pe_input=train_X[k].shape[1],
            rate=rate,
        )
        inputs.append(t_in)
        flat.append(t_flat)

    if components > 1:
        merge = concatenate(flat, axis=-1)  # (b, inp_seq_len, h)
    else:
        merge = flat[0]

    lstm_out = LSTM(16, activation="relu", return_sequences=True)(merge)
    dense1 = TimeDistributed(Dense(16, activation="relu"))(lstm_out)
    # dropout1 = Dropout(0.2)(dense1)
    output = TimeDistributed(Dense(1))(dense1)

    model = Model(inputs=inputs, outputs=output)
    model.compile(loss='mse', optimizer='adam')
    return model


def build_multilevel_transformer_unequal(
    inp_seq_len, inp_features, tgt_seq_len, **kwargs
):
    """
    input sequence length does not have to be same as the target
    sequence length; required for short term forecasting where
    window length is greater than the forecast horizon

    """
    num_layers = kwargs.get("num_layers", 2)
    d_model = kwargs.get("d_model", 128)
    num_heads = kwargs.get("num_heads", 8)
    dff = kwargs.get("dff", 128)
    rate = kwargs.get("rate", 0.1)
    components = kwargs.get("components", 2)
    include_fft = kwargs.get("include_fft", False)
    seed_value = kwargs.get("seed", 100)

    #     n_outputs = train_y.shape[1]
    #     _, inp_seq_len, inp_features = train_X[0].shape
    #seed(seed_value)
#    set_seed(seed_value)

    inputs, flat = [], []
    for ii in range(components):
        t_in, t_flat = transformer_layer(
            inp_seq_len,
            inp_features,
            num_layers,
            d_model,
            num_heads,
            dff,
            inp_seq_len,
            rate,
        )
        inputs.append(t_in)
        flat.append(t_flat)

    if include_fft:
        fft_layer = FFT(inp_seq_len, 1, 1)
        fft_out = fft_layer(inputs[0])
        flat.append(fft_out)

    if components > 1:
        merge = concatenate(flat, axis=-1)  # (b, inp_seq_len, h)
    else:
        merge = flat[0]

    # convert to the target_sequence_length
    merge = Permute((2, 1), input_shape=(inp_seq_len, components * d_model))(merge)
    merge = Dense(tgt_seq_len, activation="relu")(merge)
    merge = Permute((2, 1), input_shape=(components * d_model, tgt_seq_len))(merge)

    lstm_out = LSTM(16, activation="relu", return_sequences=True)(merge)
    dense1 = TimeDistributed(Dense(16, activation="relu"))(lstm_out)
    # dropout1 = Dropout(0.2)(dense1)
    output = TimeDistributed(Dense(1))(dense1)

    model = Model(inputs=inputs, outputs=output)
    return model


def build_multilevel_transformer_double_unequal(
    inp_seq_len, inp_features, tgt_seq_len, **kwargs
):
    """
    input sequence length does not have to be same as the target
    sequence length; required for short term forecasting where
    window length is greater than the forecast horizon

    second level transformer on top of the first one

    """
    num_layers = kwargs.get("num_layers", 2)
    d_model = kwargs.get("d_model", 128)
    num_heads = kwargs.get("num_heads", 8)
    dff = kwargs.get("dff", 128)
    rate = kwargs.get("rate", 0.1)
    components = kwargs.get("components", 2)
    include_fft = kwargs.get("include_fft", False)
    seed_value = kwargs.get("seed", 100)
    future_covariates = kwargs.get("future_covariates", False)
    dim_future_cov = kwargs.get("dim_future_cov", 1)
    latent_dim = kwargs.get("latent_dim", 16)

    seed(seed_value)
#    set_seed(seed_value)

    inputs, flat = [], []
    for ii in range(components):
        t_in, t_flat = transformer_layer(
            inp_seq_len,
            inp_features,
            num_layers,
            d_model,
            num_heads,
            dff,
            inp_seq_len,
            rate,
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

    if include_fft:
        fft_layer = FFT(inp_seq_len, 1, 1)
        fft_out = fft_layer(inputs[0])
        flat.append(fft_out)

    if components > 1:
        merge = concatenate(flat, axis=-1)  # (b, inp_seq_len, h)
    else:
        merge = flat[0]
    second_level_encoder = Encoder(
        num_layers, d_model, num_heads, dff, inp_seq_len, rate
    )
    merge = second_level_encoder(merge, True, None)

    if future_covariates:
        merge = Flatten()(merge)
        state_h = Dense(latent_dim, activation="relu")(merge)
        state_c = Dense(latent_dim, activation="relu")(merge)
        encoder_states = [state_h, state_c]
        decoder_lstm = LSTM(latent_dim, activation="relu", return_sequences=True)
        lstm_out = decoder_lstm(decoder_inputs, initial_state=encoder_states)

    else:
        # convert to the target_sequence_length
        merge = Permute((2, 1), input_shape=(inp_seq_len, d_model))(merge)
        merge = Dense(tgt_seq_len, activation="relu")(merge)
        merge = Permute((2, 1), input_shape=(d_model, tgt_seq_len))(merge)
        lstm_out = LSTM(latent_dim, activation="relu", return_sequences=True)(merge)

    dense1 = TimeDistributed(Dense(16, activation="relu"))(lstm_out)
    # dropout1 = Dropout(0.2)(dense1)
    output = TimeDistributed(Dense(1))(dense1)

    model = Model(inputs=inputs, outputs=output)
    return model


def build_multilevel_transformer_double_unequal_with_rnn(
    inp_seq_len, inp_features, tgt_seq_len, **kwargs
):
    """
    input sequence length does not have to be same as the target
    sequence length; required for short term forecasting where
    window length is greater than the forecast horizon

    second level transformer on top of the first one
    combines RNN and Transformer together

    """
    rnn = kwargs.get("rnn", "lstm-lstm")
    num_layers = kwargs.get("num_layers", 2)
    d_model = kwargs.get("d_model", 128)
    num_heads = kwargs.get("num_heads", 8)
    dff = kwargs.get("dff", 128)
    rate = kwargs.get("rate", 0.1)
    components = kwargs.get("components", 2)
    include_fft = kwargs.get("include_fft", False)
    seed_value = kwargs.get("seed", 100)
    d_model2 = kwargs.get("d_model2", 16)
    d_model3 = kwargs.get("d_model3", 16)

    seed(seed_value)
#    set_seed(seed_value)

    inputs, flat = [], []
    for ii in range(components):
        t_in, t_out = rnn_layer(
            rnn.split("-")[0], inp_seq_len, inp_features, num_layers, d_model, rate
        )
        inputs.append(t_in)
        grn_i = GRN(units=d_model)
        t_out = grn_i(t_out)
        trans_encoder = Encoder(num_layers, d_model, num_heads, dff, inp_seq_len, rate)
        encoded = trans_encoder(t_out, True, None)
        grn_j = GRN(units=d_model)
        encoded = grn_j(encoded)
        flat.append(encoded)

    if include_fft:
        fft_layer = FFT(inp_seq_len, 1, 1)
        fft_out = fft_layer(inputs[0])
        flat.append(fft_out)

    merge = concatenate(flat, axis=-1)  # (b, inp_seq_len, h)
    second_level_encoder = Encoder(
        num_layers, d_model, num_heads, dff, inp_seq_len, rate
    )
    merge = second_level_encoder(merge, True, None)

    # convert to the target_sequence_length
    merge = Permute((2, 1), input_shape=(inp_seq_len, d_model))(merge)
    merge = Dense(tgt_seq_len, activation="relu")(merge)
    merge = Permute((2, 1), input_shape=(d_model, tgt_seq_len))(merge)

    lstm_out = LSTM(d_model2, activation="relu", return_sequences=True)(merge)
    dense1 = TimeDistributed(Dense(d_model3, activation="relu"))(lstm_out)
    # dropout1 = Dropout(0.2)(dense1)
    output = TimeDistributed(Dense(1))(dense1)

    model = Model(inputs=inputs, outputs=output)
    return model
