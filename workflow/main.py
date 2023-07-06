#Copyright (c) Microsoft. All rights reserved.
### Import Packages ###
import dash
import dash_bootstrap_components as dbc
### Dash instance ###

app = dash.Dash(
        __name__,
        external_stylesheets= [dbc.themes.DARKLY] ,suppress_callback_exceptions = True,prevent_initial_callbacks=True
        )
app.title = "Forecasting Framework"
