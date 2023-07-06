#Copyright (c) Microsoft. All rights reserved.
import dash
from dash import html , dcc, ctx, dash_table
from dash.dependencies import Input, Output ,State
import dash_bootstrap_components as dbc
import pandas as pd
from dash.exceptions import PreventUpdate
import json
import os
import ast
import logging

# Import master app object
from workflow.main import app

### Import utilities ###
from utilities.dboperations import dboperations
from workflow.common.common import getLoadingElement, textInputCol, dropdownTags, listToOptions, getModalPopup
from workflow.common.config import *
from workflow.common.getdata import getForecastSetupDetails, getGeographyData, getNewColumnInfo, getTransformationDetails, getSavedExperiments ,getAllScheduledExperiments
from utilities.azure.blobOperations import downloadBlob
from workflow.common.Abalation import Abalation

abalationGridHeaders = ["ExperimentTag","Algorithm","PastCovariates","FutureCovariates","Entity","TrainStart","TrainEnd","ValStart","ValEnd","TestStart","TestEnd","quantileList"]
abalationGridHeadersOptions = []
for i in abalationGridHeaders:
    abalationGridHeadersOptions.append({'name': i,'id': i,'deletable': True,'renamable': True } )

azuregeographies = getGeographyData()

layout = dbc.Container([
        html.Div([
            dbc.Row ([ 
                dbc.Col ([ 
                            html.Div([            
                                    dbc.Row([  
                                            textInputCol("Number of Experiments","numOfExperiments","number",5, "Enter number of experiments"),  
                                            dropdownTags("Select algorithms", "algorithms", 4, True, False, listToOptions(ALGORITHMS))
                                        ]),
                                    dbc.Row([  
                                            dropdownTags("Select Azure Geography", "azuregeography", 5, False, False, listToOptions(azuregeographies)), 
                                            dropdownTags("Select Permanent columns", "permanentColumns", 5, True, False, [])
                                        ]),
                                    dbc.Row([  
                                        textInputCol("Train Start Date","trainStart","text",4, "Enter in YYYY-MM-DD %H:%M:%S format"),
                                        textInputCol("Train End Date","trainEnd","text",4, "Enter in YYYY-MM-DD %H:%M:%S format")
                                    ]),
                                    dbc.Row([  
                                        textInputCol("Validation Start Date","valStart","text",4, "Enter in YYYY-MM-DD %H:%M:%S format"),
                                        textInputCol("Validation End Date","valEnd","text",4, "Enter in YYYY-MM-DD %H:%M:%S format")
                                    ]),
                                    dbc.Row([  
                                        textInputCol("Test Start Date","testStart","text",4, "Enter in YYYY-MM-DD %H:%M:%S format"),
                                        textInputCol("Test End Date","testEnd","text",4, "Enter in YYYY-MM-DD %H:%M:%S format")
                                    ]),
                                    dbc.Row([  
                                        textInputCol("Quantile List","quantileList","text",4, "For Example:[25,50,75]"),
                                    ]),
                                    dbc.Row([  
                                                dbc.Col([], width=10),
                                                dbc.Col([
                                                    html.Button(id = "abalate" , children = 'Abalate' ,n_clicks = 0, disabled=True)
                                                ], width=2)
                                                
                                        ]),
                                    getLoadingElement("abalationFileLoading"),
                                    getLoadingElement("abalationLoading"),
                                    getLoadingElement("saveExperimentsLoading"),
                                    getLoadingElement("scheduleExperimentsLoadingOutput"),
                                    dbc.Row([
                                        dbc.Col([
                                            dash_table.DataTable(id='experimentDetailsList',columns=abalationGridHeadersOptions,row_deletable=True,editable=False,
                                                                # Styling alternate rows
                                                                style_data_conditional=[{
                                                                                        'if': {'row_index': 'odd'},
                                                                                        'backgroundColor': 'rgb(220, 220, 220)',
                                                                                        }])
                                        ]) 
                                    ]),
                                    dbc.Row([  
                                                dbc.Col([], width=8),
                                                dbc.Col([
                                                    html.Button(id = "saveExperiments" , children = 'Save Experiments' ,n_clicks = 0, disabled=True)
                                                ], width=2),
                                                dbc.Col([
                                                    html.Button(id = "scheduleExperiments" , children = 'Schedule Experiments' ,n_clicks = 0, disabled=True, title="Schedules only saved experiments. Please ensure to save new experiments before scheduling. Already scheduled experiments will not be scheduled.")
                                                ], width=2)
                                                
                                        ]),
                                    
                                    getModalPopup("abalationModal","Alert",""),
                                    getModalPopup("saveablateModal","Alert",""),
                                    getModalPopup("scheduleExperimentModal","Alert","")
                                 ])
                             ])
                ])
        ])
    ] ,id="abalationContainer",fluid = True)

# ===================Abalate Method=========================
# Enable Abalation button
@app.callback(Output('abalate','disabled'),
              Input('numOfExperiments','value'),
              Input('algorithms','value'),
              Input('azuregeography','value'),
              Input('trainStart','value'),
              Input('trainEnd','value'),
              Input('valStart','value'),
              Input('valEnd','value'),
              Input('testStart','value'),
              Input('testEnd','value'),
              Input('quantileList','value'))
def enableAbalateButton(numOfExperiments,algorithms,azuregeography,trainStart,trainEnd,valStart,valEnd,testStart,testEnd,quantileList):
    if numOfExperiments is not None or algorithms is not None or azuregeography is not None or trainStart is not None or trainEnd is not None or valStart is not None or valEnd is not None or testStart is not None or testEnd is not None or quantileList is not None:
        return False
    else:
        return True

# Generate experiments and bind to grid
@app.callback([Output('abalationLoadingOutput','children'), 
              Output("abalationModalBody","children"),
              Output("abalationModal","is_open"),
              Output("experimentDetailsList","data"),
              Output("saveExperiments","disabled")],

              [Input('abalate', 'n_clicks'),Input("abalationModalClose", "n_clicks"),Input('data', 'children')],
              State('numOfExperiments','value'),
              State('algorithms','value'),
              State('trainStart','value'),
              State('trainEnd','value'),
              State('valStart','value'),
              State('valEnd','value'),
              State('testStart','value'),
              State('testEnd','value'),
              State("experimentDetailsList","data"),
              State('experimentStore','data'),
              State("permanentColumns","value"),
              State('quantileList','value'))
def abalate(clicks,abalationModalCloseClicks,inp1,numOfExperiments,algorithms,trainStart,trainEnd,valStart,valEnd,testStart,testEnd,experimentDetailsList,storeData,permanentColumns,quantileList):
    if abalationModalCloseClicks > 0 and ctx.triggered_id == "abalationModalClose" :
        return ["", "", False,experimentDetailsList,True]
    if clicks > 0:
        print("Start: Abalation process")
        # Get Time zone info
        forecastinfo = getForecastSetupDetails(storeData)
        timezone = forecastinfo["TimeZone"].values[0]

        # Load Merged file info
        experimentSetName = storeData["experimentsetname"]
        maxExperimentNumber = 0
        features_of_completed_experiments = []
        expdf = getSavedExperiments(storeData)
        if expdf is not None and len(expdf) > 0:
            experimentList = expdf
            experimentList = pd.DataFrame.from_dict(experimentList)
            maxExperimentNumber = experimentList["ExperimentNumber"].max()
            features_of_completed_experiments = experimentList["FeatureList"].unique()
        path = f'{experimentSetName}/{MERGED_FOLDER}'
        fileName = PreprocessedFileName  
        mergedData = pd.read_csv(f'{MASTER_FOLDER}/{path}/{fileName}',index_col=0)#
        mergedData.reset_index(inplace = True)
        if (pd.Timestamp(trainStart)>=pd.Timestamp(mergedData["DateTime"].min()) and pd.Timestamp(testEnd) <= pd.Timestamp(mergedData["DateTime"].max())):
            rows = generateExperiments(mergedData.columns.values.tolist(),storeData, numOfExperiments,algorithms,trainStart,trainEnd,valStart,valEnd,testStart,testEnd, maxExperimentNumber,features_of_completed_experiments,permanentColumns,quantileList)
        else:
            return ["", "Enter valid dates, dates should be in range of source data. Starting date: "+ str(mergedData["DateTime"].min())+". Dataset End date: "+ str(mergedData["DateTime"].max()), True, experimentDetailsList,True]
        
        rows = rows.to_dict("records")
        print("End: Abalation process")
        print(rows)
        return ["", "", False, rows,False]
    elif ctx.triggered_id == "data":
        #Load the existing saved experiments, if they are not scheduled 
        try:
            print("Loading saved experiments")
            expdf = getSavedExperiments(storeData)
            return [dash.no_update, dash.no_update , dash.no_update,expdf,True]
        except Exception as ex:
            print(ex)
            logging.info("Error in loading saved experiments")
            raise PreventUpdate()
    else:
        raise PreventUpdate()

def getColumnAndTags(newColsdataDF,transData,mergedDataColumns):
    
    df = transData

    newColsdataDF = newColsdataDF[['Name','Tag']]
    newColsdataDF.rename(columns={'Name':'ColumnName'},inplace = True)

    finalDF = pd.concat([df,newColsdataDF],axis = 0 )
    
    cols =  finalDF['ColumnName'].unique()
    tagCols= finalDF.groupby('ColumnName').agg(list)
    tagCols = tagCols.reset_index()
    tagColsBinding = {}
    for col in mergedDataColumns:
        if col in cols:
            tagColsBinding[col] = tagCols[tagCols["ColumnName"]==col]['Tag'].values[0][0]
        else:
            tagColsBinding[col] = ""

    return tagColsBinding

# Generate list of experiments
def generateExperiments(mergedDataColumns,storeData,numOfExperiments,algorithms,trainStart,trainEnd,valStart,valEnd,testStart,testEnd, maxExperimentNumber,features_of_completed_experiments,permanentColumns,quantileList):
    rows = []
    # Read column information
    newColsdata = getNewColumnInfo(storeData)
    newColsdataDF = pd.DataFrame(newColsdata , columns= ['Name','Tag','ColumnList'])
    newColsList = newColsdataDF["Name"].values.tolist()
    #Read transformation data
    transdata = getTransformationDetails(storeData)
    transDataDf = pd.DataFrame(transdata)
    transformdata = transDataDf['Transformations'].values
    df = pd.DataFrame()
    for i in range(len(transformdata)):
        jsn =  json.loads(transformdata[i])
        df1 = pd.DataFrame(jsn)
        df = pd.concat([df,df1] ,axis = 0)
    df.rename(columns = {'ColumnTag' : 'Tag'} ,inplace = True)
    df['ColumnName'] = df['FileIdentifier'] + '_' + df['ColumnName']
    transDataDf = df
    
    # Identify Entity field
    entityFile = transDataDf[transDataDf["FileType"] == "Entity"]
    entityField = entityFile["ColumnName"].values[0]

    # Filter fields from the master list for abalation
    mergedDataColumns.remove(entityField)
    mergedDataColumns.remove("DateTime")
    if 'AvailableTime' in mergedDataColumns :
        mergedDataColumns.remove("AvailableTime")
    
    # Delete entity field
    if entityField in permanentColumns:
        permanentColumns.remove(entityField)

    # Get column to tag mapping
    columnTagsDict = getColumnAndTags(newColsdataDF,transDataDf[['ColumnName','Tag']],mergedDataColumns)

    # Perform abalation
    al = Abalation(columnTagsDict, numOfExperiments, maxExperimentNumber, algorithms,features_of_completed_experiments)
    experiments_dict = al.overall_feature_combinations(permanentColumns)
    experiments_dict = pd.DataFrame(experiments_dict, columns=["ExperimentTag","Algorithm","FeatureList"])
    experiments_dict['FeatureList'] = experiments_dict['FeatureList'].astype('str')
    # Prepare rows for grid
    rows = experiments_dict.copy()
    rows["PastCovariates"] = ""
    rows["FutureCovariates"] = ""
    for exp in experiments_dict.iterrows():
        index = exp[0]
        exp = exp[1]
        featureList = ast.literal_eval(exp["FeatureList"])
        exp["PastCovariates"] = []
        exp["FutureCovariates"] = []
        # Identify past covariates
        for col in featureList:
            if col not in newColsList:
                fileIdentier = col.split("_")[0]
            else:
                sourceField = ast.literal_eval(newColsdataDF[newColsdataDF["Name"]==col]['ColumnList'].values[0])
                sourceField = sourceField[0]
                fileIdentier = sourceField.split("_")[0]
            FileType = transDataDf[transDataDf["FileIdentifier"]==fileIdentier]["FileType"].values[0]
            if FileType == "PastCovariates":
                exp["PastCovariates"].append(col)
            elif FileType == "FutureCovariates":
                # Identify future covariates
                exp["FutureCovariates"].append(col)
        rows.loc[index,["PastCovariates"]] = str(exp["PastCovariates"])
        rows.loc[index,["FutureCovariates"]] = str(exp["FutureCovariates"])

    # Divide feature list into past and future covariates
    rows["TrainStart"] = trainStart
    rows["TrainEnd"] = trainEnd
    rows["ValStart"] = valStart
    rows["ValEnd"] = valEnd
    rows["TestStart"] = testStart
    rows["TestEnd"] = testEnd
    rows["Entity"] = entityField
    rows["quantileList"] = str(quantileList)
    return rows

#=======================Save Experiments List=====================
@app.callback( Output("saveExperimentsLoadingOutput","children"), 
        Output("scheduleExperiments","disabled"),
        Output("saveablateModalBody","children"),
        Output("saveablateModal","is_open"), 
        Input("saveablateModalClose", "n_clicks"),
        Input("saveExperiments","n_clicks"),
        Input('data', 'children'),
        State("experimentDetailsList","data"),
        State('experimentStore','data'),
        State('azuregeography','value')
    )
def saveExperiments(saveablateclick,clicks,dfD,experimentDetailsList,storeData,azuregeography):
    if saveablateclick > 0 and ctx.triggered_id == "saveablateModalClose":
        return "",False,"",False
    if clicks > 0:
        print(getSavedExperiments(storeData))
        print(getSavedExperiments(storeData))
        store_df = pd.DataFrame.from_dict(getSavedExperiments(storeData))
        count_stored_experiment = 0
        if len(store_df) != 0:
            for i in range(len(experimentDetailsList)):
                if experimentDetailsList[i]['ExperimentTag'] in store_df['ExperimentTag'].unique():
                    count_stored_experiment+=1
        current_experiment_count = len(experimentDetailsList)
        if current_experiment_count==count_stored_experiment:
            return "",False,"No new experiments were saved.",True
        else:
            if azuregeography is not None and type(azuregeography) == str:
                # Save the Azure geography to database
                dboperations.executeStoredProcedure(SAVE_GEOGRAPHY_INFO_SP ,"@ExperimentSetID = ?, @GeographyName = ? ",(storeData["experimentsetid"],azuregeography),"dbo",0)

            for row in experimentDetailsList:
                # Delete all records in database
                dboperations.executeStoredProcedure(DELETE_EXPERIMENTS_LIST_SP ,"@ExperimentSetID = ?, @ExperimentTag = ? ",(storeData["experimentsetid"], row["ExperimentTag"]),"dbo",0)

                # Save forecast details to database
                dboperations.executeStoredProcedure(SAVE_EXPERIMENTS_LIST_SP,"@ExperimentSetID = ? ,@ExperimentTag = ?,@Algorithm =? ,@PastCovariates = ?,@FutureCovariates = ?,@Entity = ?,@TrainStart = ?,@TrainEnd = ?,@ValStart = ?,@ValEnd =? ,@TestStart = ?,@TestEnd = ? , @quantileList = ?",(storeData["experimentsetid"], row["ExperimentTag"],row["Algorithm"],row["PastCovariates"],row["FutureCovariates"],row["Entity"],row["TrainStart"],row["TrainEnd"],row["ValStart"],row["ValEnd"],row["TestStart"],row["TestEnd"],row["quantileList"]),"dbo",0)

            return "", False,DATA_SAVE_MESSAGE,True
    elif ctx.triggered_id == "data":
        expdf = getSavedExperiments(storeData)
        if len(expdf) > 0:
            #Enable scheduler button
            return "",False,"",False
    # elif ctx.triggered_id == "abalate":
    #     #Disable Schedule till new exp are saved
    #     return "",True,"",False
    else:
        raise PreventUpdate()

#=======================Schedule experiments============
@app.callback(Output("scheduleExperimentsLoadingOutput","children"),
              Output("scheduleExperimentModalBody","children"),
              Output("scheduleExperimentModal","is_open"),
    Input("scheduleExperiments","n_clicks"),
    Input("scheduleExperimentModalClose","n_clicks"),
    State('experimentStore','data'),
    State("experimentDetailsList",'data')
)
def scheduleExperiments(clicks,scheduleModalClose,storeData,experimentDetailsList):
    
    if scheduleModalClose>0 and ctx.triggered_id == 'scheduleExperimentModalClose':
            return "","",False
    if clicks > 0: 
        store_df = pd.DataFrame.from_dict(getAllScheduledExperiments(storeData))
        count_stored_experiment = 0
        if len(store_df) !=0 :
            for i in range(len(experimentDetailsList)):
                if experimentDetailsList[i]['ExperimentTag'] in store_df['experimenttag'].unique():
                    count_stored_experiment+=1
        print(len(experimentDetailsList))
        print(count_stored_experiment)
        current_experiment_count = len(experimentDetailsList)
        if current_experiment_count==count_stored_experiment:
            return "","No new experiments were scheduled.",True
        else:
            dboperations.executeStoredProcedure(SCHEDULE_EXPERIMENTS_LIST_SP ,"@ExperimentSetID = ?",(storeData["experimentsetid"]),"dbo",0),"",False
            return "",DATA_SAVE_MESSAGE,True
# ==========================page load method==================
@app.callback(Output('abalationFileLoadingOutput','children'), Output("permanentColumns","options"),
                [Input('data', 'children')],
              State('experimentStore','data'),
              State('siteSetupNavigation', 'value'))
def onTabLoad(inp1, storeData,val):
    print("Executing tab 8 page load")
    columnList = []
    if val == "tab-8":
        fileName = PreprocessedFileName
        experimentSetName = storeData["experimentsetname"]
        path = f'{MASTER_FOLDER}/{experimentSetName}/{MERGED_FOLDER}'#
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            downloadBlob(f'{path}/{fileName}',"")
            mergeDF = pd.read_csv(f'{path}/{fileName}',index_col=0)
            columnList = mergeDF.columns.values.tolist()
            if 'AvailableTime' in columnList :
                columnList.remove('AvailableTime')
        except Exception as ex:
            print(ex)            
        return "", listToOptions(columnList)
    else:
        raise PreventUpdate()