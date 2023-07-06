#Copyright (c) Microsoft. All rights reserved.
### Import Packages ###
import dash
from dash import dcc ,html,ALL
from dash.dependencies import Input, Output,State
import pandas as pd
from workflow.pages.transformations import *
import numpy as np 

### Import Dash Instance ###
from workflow.main import app
from utilities.azure import blobOperations

from workflow.common import getdata,common
from workflow.common.common import * 
from workflow.common.config import *
from utilities.dboperations import dboperations

joinList = ['inner' , 'left' , 'right','outer']
joinoptions = listToOptions(joinList)

createColsList = ['ColumnCreator','Columns','Name','Interpolation','Tag','Params']
createColsOptions = []
for i in createColsList:
    createColsOptions.append({'name': i,'id': i,'deletable': True,'renamable': True } )

def step(id,filesoptions):
    return html.Div(
        children=[
            dbc.Row([ dbc.Col([ 
            dcc.Dropdown(placeholder = 'Join Operator' , options=joinoptions, id={"operator": str(id)}),
            dcc.Dropdown(placeholder = 'Select File',options=filesoptions, id={"file": str(id)}),
            ] , width = 4)])
        ])

layout = html.Div(
    children=[
        html.Button('Generate Merge Sequence', id='add_step_button', n_clicks_timestamp=0,n_clicks = 0 ),
        dcc.Store(id = 'sourceDataMerge', storage_type = 'memory'),
        html.Div(children=[], id='initFileTag'),
        dcc.Store(id = 'filesToMergeVariable' , data = []),
        html.Div(children=[], id='step_list'),
        html.Button('Merge Files', id='merg_button', n_clicks_timestamp=0,n_clicks = 0 , disabled=True),
        html.Div(id = 'uploadMessage', style={'display':'none'}) ,
        getModalPopup("mergeFileModal","Alert",""),
        html.Div(id = 'fileLoadMessage') ,
        getLoadingElement("mergePageLoading"),
        getLoadingElement("mergefilesLoading"),
        ]
        )


@app.callback(
    dash.dependencies.Output('initFileTag', 'children'),
    dash.dependencies.Output('filesToMergeVariable', 'data'),
    dash.dependencies.Output('step_list', 'children'),
    dash.dependencies.Output('add_step_button', 'disabled'),
    dash.dependencies.Output('merg_button', 'disabled'),
    dash.dependencies.Input('add_step_button', 'n_clicks'),
    dash.dependencies.State('step_list', 'children'),
    dash.dependencies.State('sourceDataMerge','data'),

    prevent_initial_callback = True
    )
def add_step(clicks,div_list,sourcefileTypes):
    if clicks > 0  :
        filesOptions = listToOptions(sourcefileTypes)
        for i in list(range(2,len(sourcefileTypes)+1)):
            div_list += [step(i,filesOptions)]
        initFileTag = html.Div(dbc.Row ([ dbc.Col ([dcc.Dropdown(placeholder = 'Select File',options=filesOptions,id= "initFile" ) ] ,width = 4) ]) )
    return initFileTag,sourcefileTypes,div_list,True,False


def performMergeOperations(initFile,operators,fileIdentifiers,targetTimezone, SourcePath="",listDF=None):
    # If there is a list of dataframes
    if listDF is None:
        _,df1,_ = blobOperations.getBlobDf("default",SourcePath,initFile+'.csv') 
    else:
        df1 = listDF[0]

    df1['DateTime'] = pd.to_datetime(df1['DateTime'], utc=True).map(lambda x: x.tz_convert(targetTimezone))
    df1 = df1.set_index(pd.DatetimeIndex(df1['DateTime']) )
    del df1['DateTime']
    for id in range(len(operators)):
        # If there is a list of dataframes
        if listDF is None:
            _,df2,_ = blobOperations.getBlobDf("default",SourcePath,fileIdentifiers[id]+'.csv')
        else:
            df2 = listDF[id+1]
        df2['DateTime'] = pd.to_datetime(df2['DateTime'], utc=True).map(lambda x: x.tz_convert(targetTimezone))
        df2 = df2.set_index(pd.DatetimeIndex(df2['DateTime']) )
        del df2['DateTime']
        if 'AvailableTime' in df1.columns  and  'AvailableTime' in df2.columns:
            del df2['AvailableTime']

        df1 = df1.join(df2,how = f'{str(operators[id])}')
    print(df1)
    return df1

@app.callback( Output("mergefilesLoading","children"),
    Output("uploadMessage",'children'),
    Output("mergeFileModalBody","children"),
    Output("mergeFileModal","is_open"),
    Input("merg_button",'n_clicks'),
    Input("mergeFileModalClose", "n_clicks"),
    Input("initFile",'value'),
    [Input({"operator": ALL}, "value")],
    [Input({"file": ALL}, "value")],
    State('experimentStore','data'),
    prevent_initial_callback = True
    )
def sourcefiletable1(clicks,closeClicks,*args):
    if closeClicks > 0 and ctx.triggered_id == "mergeFileModalClose":
        return "",dash.no_update,"",False
    if clicks > 0 : 
        initFile = args[0]
        operators = args[1]
        fileIdentifiers = args[2]
        data = args[3]
        experimentSetName = data["experimentsetname"]
        transformpath = f'{experimentSetName}/{TRANSFORM_CLEANED_FOLDER}'
        mergepath = f'{experimentSetName}/{MERGED_FOLDER}'
        SourcePath = f'{MASTERCONTAINER}/{MASTER_FOLDER}/{transformpath}' 
        TargetPath = f'{MASTER_FOLDER}/{mergepath}' 
        df1 = performMergeOperations(initFile,operators,fileIdentifiers,targetTimezoneMergeFile,SourcePath,None)
        df1.to_csv(os.path.join(TargetPath,MergedFileName),index_label='DateTime')
        try : 
            # Delete all records in database
            dboperations.executeStoredProcedure(DELETE_MERGEFILE_SP,"@ExperimentSetID = ? ",(data["experimentsetid"]),"dbo",0) 
            # Save timezone details to database
            dboperations.executeStoredProcedure(INSERT_MERGEFILE_SP ,"@ExperimentSetID = ? ,@initFile=?, @operators = ?, @fileIdentifiers= ?",(data["experimentsetid"], initFile, json.dumps(operators), json.dumps(fileIdentifiers)),"dbo",0)
            print("Saved merge sequence in database information!")
            
            blobOperations.uploadBlob(os.path.join(TargetPath,MergedFileName))
        except Exception as e:
            # Raise exception here...testing the uploading 
            print('Error while uploading')
        return "",'Success',DATA_SAVE_MESSAGE,True
    else :
        raise PreventUpdate()


@app.callback(Output('sourceDataMerge','data'),
                Output('tab-6','disabled'),
                Output("mergePageLoadingOutput","children"),
                Output("fileLoadMessage","children"),
                [Input('data', 'children'),Input("uploadMessage",'children')],
              State('experimentStore','data'))
def onTabLoad(inp1, uploadMessage,data):
    if ctx.triggered_id == "uploadMessage" and uploadMessage == "Success":
        return dash.no_update,False,dash.no_update, ""
    global targetTimezoneMergeFile
    print("Executing tab 5 page load")
    sourceData = getdata.getTimezoneDetails(data)
    fileTypes = []
    for file in sourceData:
        fileTypes.append(file['FileIdentifier'])
    tabDisabled = True
    fileLoadMessage = ""
    # Download the Merged file if already exists
    fileName = MergedFileName
    experimentSetName = data["experimentsetname"]
    path = f'{MASTER_FOLDER}/{experimentSetName}/{MERGED_FOLDER}'#

    storeDataValue = getdata.getForecastSetupDetails(data)
    targetTimezoneMergeFile = str(storeDataValue.iloc[0,:]['TimeZone'])

    try:
        if not os.path.exists(path):
            os.makedirs(path)
        blobOperations.downloadBlob(f'{path}/{fileName}',"")
        tabDisabled = False
        fileLoadMessage = "Merged File is already available, you can proceed to next tab or regenerate!"
    except Exception as ex:
        fileLoadMessage = "Merged File is not available, proceed to generate sequence!"
        print("Merged File doesn't exist")
        print(ex)
    return fileTypes,tabDisabled,"",fileLoadMessage
