#Copyright (c) Microsoft. All rights reserved.
from dash import html , dcc
import dash_bootstrap_components as dbc
import re

# Check Special Characters
def detect_special_characer(pass_string):
    regex= re.compile('[@_!#$%^&*()<>?/\|}{~:]')
    if(regex.search(pass_string) == None):
        res = False
    else:
        res = True
    return(res)
    
def listToOptions(lst):
    options = []
    for i in lst:
        options.append({'label': i,'value': i } )
    return options

fileTypeList = ['Entity', 'PastCovariates' , 'FutureCovariates' ]

def dropdownTags(labelName,idName,width,multi=False,disabled = False,options=[]):
    return dbc.Col([
                    html.Label(labelName),
                    dcc.Dropdown(id = idName,multi=multi ,disabled = disabled,options=options)
                ],width = width)

def btnTags(btnName,idName,width,disabled = False):
    return dbc.Col([ html.Button(btnName,id = idName,n_clicks = 0,disabled = disabled, className="btnCls")
                ], width = width)

def getLoadingElement(idName):
    return dcc.Loading(
                        id=idName,
                        className = "loading",
                        children=[html.Div([html.Div(id=idName+"Output",className = "loadingDiv")])],
                        type="default")

def textInputCol(label,id,type,width,placeholder):
    return dbc.Col([
                    html.Label(label),
                    dcc.Input( id = id,type = type,placeholder = placeholder)
                ],width = width)

def getModalPopup(id,title,content):
    return dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle(title)),
                dbc.ModalBody(content, id=id+"Body"),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id=id+"Close", className="ms-auto", n_clicks=0
                    )
                ),
            ],
            id=id,
            is_open=False,
        )