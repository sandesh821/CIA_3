#Copyright (c) Microsoft. All rights reserved.
### Import Packages ###
import dash
from dash import dcc ,html
from dash.dependencies import Input, Output

### Import Dash Instance ###
from workflow.main import app

#dash.register_page(__name__,path = '/')

layout = html.Div([ html.H1('Display Error Tracking') ])