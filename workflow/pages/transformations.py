#Copyright (c) Microsoft. All rights reserved.
import dash
from dash import html , dcc, ctx
from dash.dependencies import Input, Output ,State
import dash_bootstrap_components as dbc
import pandas as pd
from dash.exceptions import PreventUpdate
from dash import dash_table as dt
import json
import os
import shutil

### Import Dash Instance ###
from workflow.main import app

### Import Packages ###
from workflow.common.FixTime import *
from workflow.common.PrepopulateTransformations import *
from workflow.common.UnivariatePlotly import * 
from workflow.common.common import *
from workflow.common import getdata,ColumnarTransformations
from workflow.common.config import *
from workflow.common.InterpolatorMethods import * 

### Import utilities ###
from utilities.azure import blobOperations
from utilities.dboperations import dboperations

def loadTimeZoneOptions():
    timezoneDF = dboperations.executeStoredProcedure(GET_TIMEZONES_SP,None,None,"dbo",2)
    return timezoneDF
timezoneDf  = loadTimeZoneOptions()
timezoneDf['UTC'] = timezoneDf['UTC offset'].apply(lambda i : i[4:7]).astype('int')

def srcFileToDF(filetype,sourceData):
    source_files_df = pd.DataFrame(sourceData)  # this should be from DB or file, check with Team????
    source_files_df = source_files_df[source_files_df['FileType'] ==filetype]
    filenames = source_files_df['FileIdentifier'].unique() 
    filenames_options = listToOptions(filenames) 
    return source_files_df,filenames_options

def getColList(FileType,FileName,sourceData):
    df,_ = srcFileToDF(FileType, sourceData)
    df1 = df[df['BlobName'] ==  FileName].copy()
    AccountName = df1['AccountName'].values[0]
    ContainerName = df1['ContainerName'].values[0]
    BlobName = df1['BlobName'].values[0]
    _,_,cols = blobOperations.getBlobDf(AccountName,ContainerName,BlobName) 
    col_list_options = listToOptions(cols) 
    return cols,col_list_options

fileTypeOptions = listToOptions(fileTypeList) 

sourceData = None

trsfrm_tbl_col_list = ["FileType","FileIdentifier" ,"ColumnName","TransformationType","Operator","TransformationValue"]
trsfrm_tbl_col_options = []
for i in trsfrm_tbl_col_list:
    trsfrm_tbl_col_options.append({'name': i,'id': i,'deletable': True,'renamable': True,'editable' :True } )

tz_tbl_col_list = ["FileIdentifier","FileType","FileName" ,'DateTimeColumnName','DateTimeTZType','DateTimeTZAware','DateTimeTZConversionUnit','AvailColumnName','AvailTZType','AvailTZAware','AvailTZConversionUnit']
tz_tbl_col_options = []
for i in tz_tbl_col_list:
    tz_tbl_col_options.append({'name': i,'id': i,'deletable': True,'renamable': True } )

transform_list = ["lower_capping","upper_capping" ,"filter","scale","replace"] 
transform_options =  listToOptions(transform_list) 

operator_list = ["In" ,"Not In" ,"Multiply","Divide" ,"Other"] 
operator_options =  listToOptions(operator_list) 

timezoneTypeList = ['Standard','UnixTime','Timezone','Local']
timezoneTypeOptions = listToOptions(timezoneTypeList) 

viz_list = ["cdf_graph" ,"pdf_graph" ,"boxplot_graph","line_graph" ] 
viz_options =  listToOptions(viz_list) 

def returnOptions(value):
    if value == 'UnixTime':
        options = listToOptions(['ns','ms','s'])
    elif value == 'Standard' :
        options = [{'label': 'Yes','value': True },{'label': 'No','value': False }]
    elif value == 'Timezone' :
        options = [{'label': 'Yes','value': True },{'label': 'No','value': False }]
    elif value == 'Local' :
        options = [{'label': 'Yes','value': True },{'label': 'No','value': False }]
    return options

def getDF(forecastTZ,df,fileType,selectDatetimeDropdown,checkDatetimeTypeDropdown,dateTimeConversion,TZConversionDropdown,
                        selectAvailDatetimeDropdown=None,checkAvailDatetimeTypeDropdown=None,availDatetimeConversion=None,AvailTZConversionDropdown =None): 
    datetime_col_options = {'type': checkDatetimeTypeDropdown, 'tz_aware': dateTimeConversion, 'tz_info':TZConversionDropdown}
    datetime_col = selectDatetimeDropdown
    if fileType == 'FutureCovariates':
        availdatetime_col_options = {'type': checkAvailDatetimeTypeDropdown, 'tz_aware':availDatetimeConversion, 'tz_info':AvailTZConversionDropdown}
        availdatetime_col = selectAvailDatetimeDropdown
        ft = FixTime(forecastTZ, df, datetime_col, datetime_col_options,availdatetime_col,availdatetime_col_options)
        series1,series2  = ft.apply()
        df1 = pd.DataFrame(series1,columns=[selectDatetimeDropdown ])
        df2 = pd.DataFrame(series2,columns=[selectAvailDatetimeDropdown ])
        del df[selectDatetimeDropdown ]
        del df[selectAvailDatetimeDropdown ]
        df1 = pd.concat([df1,df2],axis = 1)
    else : 
        ft = FixTime(forecastTZ, df, datetime_col, datetime_col_options)
        series1,_  = ft.apply()
        df1 = pd.DataFrame(series1,columns=[selectDatetimeDropdown])
        del df[selectDatetimeDropdown ]
    finalDF = pd.concat([df1,df],axis = 1)
    #finalDF = finalDF[[selectDatetimeDropdown,column]]
    finalDF['DateTime' ] = pd.to_datetime(finalDF[selectDatetimeDropdown ])
    finalDF['Year'] = finalDF['DateTime' ].dt.year
    finalDF['Month'] = finalDF['DateTime' ].dt.month
    finalDF['Date'] = finalDF['DateTime'].dt.date
    return finalDF

def genStore(storename):
    return dcc.Store(id = f'{storename}' , data = [],storage_type = 'session')

trsfrm_tbl_cols = ['FileType','FileIdentifier','FileDetails','ColumnName','ColumnTag','Resampler','InterpolationClass','InterpolationMethod','ApplyTransformFlag']
trsfrm_tbl_options = []
for i in trsfrm_tbl_cols:
    trsfrm_tbl_options.append({'name': i,'id': i,'deletable': True,'renamable': True } )


interpolMethodObj = InterpolatorMethods()
interpolateClass = ['pandas','others']
interpolateClassOptions = listToOptions(interpolateClass)
interpolateMethods = {'pandas' : interpolMethodObj.pandas_methods ,'others' : interpolMethodObj.extra_methhods}

resample_list = ['max','mean']
resample_options = listToOptions(resample_list)

apply_transform_flag_list = ['Yes','No']
apply_transform_flag_options = listToOptions(apply_transform_flag_list)

def getFileName(FileIdentifier,sourceData):
    source_files_df = pd.DataFrame(sourceData) 
    sourceDataDF = source_files_df[source_files_df['FileIdentifier'] == FileIdentifier ]
    FileName = sourceDataDF['BlobName'].values[0]
    return FileName
    
layout = html.Div([
                        html.Div([
                            dbc.Row([ 
                                 dbc.Col([
                                        html.B('TIMEZONE CONVERSION', className="sectionHeader")
                                 ])
                            ]),
                            dbc.Row([  
                                dbc.Col([
                                    html.Label('File Type'),
                                    dcc.Dropdown(id = 'FileType',options = fileTypeOptions) ,
                                ],width = 4),
                                dropdownTags('File Identifier','FileIdentifier',4)
                            ]),
                            getModalPopup("timezoneValidationModal","Alert",""),
                            getModalPopup("saveTZModal","Alert",""),
                            genStore('FileName'),
                            getLoadingElement("fileLoading"),
                            getLoadingElement("fileFutureCovLoading"),
                            genStore('selectDatetimeDropdownStore'),
                            genStore('checkDatetimeTypeDropdownStore'),
                            genStore('dateTimeConversionStore'),
                            genStore('TZConversionDropdownStore'),

                            genStore('selectApplDatetimeDropdownStore'),
                            genStore('checkApplDatetimeTypeDropdownStore'),
                            genStore('applDatetimeConversionStore'),
                            genStore('applTZConversionDropdownStore'),

                            genStore('selectAvailDatetimeDropdownStore'),
                            genStore('checkAvailDatetimeTypeDropdownStore'),
                            genStore('availDatetimeConversionStore'),
                            genStore('AvailTZConversionDropdownStore'),
                            html.Div(id = 'futureCovComponents'),
                            dbc.Row([ dbc.Col([],width=10), btnTags("Apply",'convertTimeButton',width=2)]) ,
                            html.Div(id = 'conversionMessage'),
                            getLoadingElement("timezoneDetailsLoading"),
                            dbc.Row([
                                    dbc.Col([
                                        dt.DataTable(
                                        id='timezoneConversionTable',
                                        columns=tz_tbl_col_options,
                                        editable=False,
                                        row_deletable=True,
                                        # Styling alternate rows
                                        style_data_conditional=[{
                                                                'if': {'row_index': 'odd'},
                                                                'backgroundColor': 'rgb(220, 220, 220)',
                                                                }]
                                    )
                                    ]) ]),
                            getLoadingElement("timezoneDetailsSaveLoading"),
                            dbc.Row([
                                dbc.Col([],width=10),
                                btnTags("Save Timezone Info",'saveTimezoneButton',2,disabled=True)
                            ])
                        ], id="dateFieldSelectionSection"),
                        html.Div([
                            dbc.Row([ 
                                 dbc.Col([
                                        html.B('COLUMN LEVEL EDA', className="sectionHeader")
                                 ])
                            ]),
                            dbc.Row([ 
                                dropdownTags('Select Column','edaColListDropdown',width=3,multi = False),
                                dropdownTags('Visualization Type','vizTypeDropdown',width=3,multi = True, disabled = True),
                                dbc.Col([],width=4),
                                btnTags("Generate",'edaButton',width=2,disabled=True)
                                ], className="visualizationSelection")  ,
                            getLoadingElement("graphLoading"),
                            dbc.Row([ 
                                    html.Div(children=[],id = 'graphComponent'),
                                ]),
                            dcc.Store(id='checklist') ,
                            dcc.Store(id='entitytype') ,
                            dcc.Store(id='granularityStore'),
                        ], id="edaSection"),
                        dcc.Store(id = 'activecellStore', storage_type = 'memory'),
                        html.Div([
                        dbc.Row([ 
                                 dbc.Col([
                                        html.B('TRANSFORMATION CONFIGURATION', className="sectionHeader")
                                 ])
                        ]),
                        dbc.Row([ 
                                dropdownTags('Column Name','colListDropdown',2),
                                dropdownTags('Column Tag','ColumnTag',2),
                                dropdownTags('Select Resampler','resampleDropdown',2),
                                dropdownTags('Interpolation Class','interpolateClass',2),
                                dropdownTags('Interpolation Method','interpolateMethod',2),
                                dropdownTags('Apply All Transformations','applytransformDropdown',2),
                                dbc.Col([],width=8),
                                btnTags("Add",'addtransformBtn1',2,True) ,
                                btnTags("Save",'saveTransform',2,True)      
                        ], id="table1Inputs"),
                        getLoadingElement("table1Loading"),
                        genStore('transformationStore'),
                        dbc.Row([
                                 dbc.Col([
                                    dt.DataTable(
                                        id='addTransformTable',
                                        columns=trsfrm_tbl_options,
                                        editable=False,
                                        row_deletable=True,
                                        # Styling alternate rows
                                        style_data_conditional=[{
                                                                'if': {'row_index': 'odd'},
                                                                'backgroundColor': 'rgb(220, 220, 220)',
                                                                }],
                                        style_cell_conditional=[
                                            {'if': {'column_id': 'FileDetails',},
                                                'display': 'None',}]   
                                    )
                            ]) 
                        ]),
                        getModalPopup("transformationValidationModal","Alert",""),
                        getModalPopup("saveTransformationModal","Alert",""),
                        dbc.Row([
                                    html.I('***Note : Transformations Executes in the below given order***')
                                 ]),
                        dbc.Row([ 
                                dropdownTags('Select Transformations','transformDropdown',2),
                                dbc.Col([html.Div(id = 'OperatorTag')] ,width = 2) ,
                                # operatorDropdown is loaded dynamically in code
                                dbc.Col([ 
                                    html.Label('Transform Value'),
                                    dcc.Input( id = 'transformValue',type = 'text',style = {'width': '100%'})
                                ],width = 2),
                                btnTags("Add More",'addTransformListBtn',2,disabled=True),
                                btnTags("Save",'saveColumnTransformations',2,disabled=True) ,
                        ]),
                        getLoadingElement("table2TransformationLoading"),
                        genStore('table2TransformationStore'),
                        dbc.Row([
                                 dbc.Col([
                                    dt.DataTable(
                                        id='addTransformListToTable',
                                        columns=trsfrm_tbl_col_options,
                                        editable=True,
                                        row_deletable=True,
                                        # Styling alternate rows
                                        style_data_conditional=[{
                                                                'if': {'row_index': 'odd'},
                                                                'backgroundColor': 'rgb(220, 220, 220)',
                                                                }]
                                    )
                            ]) 
                        ]),
                        getLoadingElement("transformationLoading"),
                        dbc.Row([
                            dbc.Col([],width=10),
                            btnTags("Transform",'transformActionButton',2,disabled=True)
                        ])
                        ], id="transformationSection"),
                        getModalPopup("saveColumnTransformModal","Alert",""),
                        getModalPopup("columnTransformValidationModal","Alert",""),
                        getModalPopup("transformActionModal","Alert",""),
            dcc.Store(id = 'sourceData', storage_type = 'session'),
            html.Link(
                rel='stylesheet',
                href='/static/transformationstylesheet.css?v=6'
            )
        ])

@app.callback(Output('interpolateMethod','options'),
                Input('interpolateClass','value'))
def loadInterpolationMethods(interpolationClass):
    if interpolationClass is not None :  #UNDO
        options = listToOptions( interpolateMethods[interpolationClass])
        return options
    else : 
        raise PreventUpdate()

@app.callback(Output("saveColumnTransformModalBody","children"),
    Output("saveColumnTransformModal","is_open"),
    Output('table2TransformationStore','data'), 
    Output("table2TransformationLoadingOutput","children"),
    Output("transformActionButton","disabled"),
    Input('saveColumnTransformations', 'n_clicks'),
    Input('data', 'children'),
    Input("saveColumnTransformModalClose", "n_clicks"),
    State('addTransformListToTable','data'),
    State('table2TransformationStore','data'),
    State('experimentStore','data')
    )
def saveTransforTable2(n_clicks,inp1,closeClicks,tableData,table2TransformationData,storeData):
    if closeClicks > 0 and ctx.triggered_id == "saveColumnTransformModalClose":
        return "",False,dash.no_update, dash.no_update,dash.no_update
    if n_clicks > 0 :
        if len(table2TransformationData) == 0:
            table2TransformationData = {}

        if len(tableData) ==0 :
            dboperations.executeStoredProcedure(DELETE_COLUMN_TRANSFORMATION_DETAILS_SP,"@ExperimentSetID = ?, @FileIdentifier=?, @ColumnName=? ",(storeData["experimentsetid"],FileIdentifier,ColumnName),"dbo",0)
            return DATA_SAVE_MESSAGE,True,tableData,"",False
        else : 
            fileIdentifier = tableData[0]["FileIdentifier"]
            columnName = tableData[0]["ColumnName"]

            # Update local store to maintain the data with recent updates as well
            if fileIdentifier not in table2TransformationData.keys():
                table2TransformationData[fileIdentifier] = {}
            table2TransformationData[fileIdentifier][columnName] = json.dumps(tableData)
            try:
                # Delete all records in database
                dboperations.executeStoredProcedure(DELETE_COLUMN_TRANSFORMATION_DETAILS_SP,"@ExperimentSetID = ?, @FileIdentifier=?, @ColumnName=? ",(storeData["experimentsetid"],fileIdentifier,columnName),"dbo",0)

                inputDict = json.dumps(tableData)
                # Save forecast details to database
                dboperations.executeStoredProcedure(SAVE_COLUMN_TRANSFORMATION_DETAILS_SP ,"@ExperimentSetID = ? ,@FileIdentifier=?, @ColumnName=?,@Transformations = ?",(storeData["experimentsetid"],fileIdentifier,columnName, inputDict),"dbo",0)
                
                print("Saved transformation data information!")
                return DATA_SAVE_MESSAGE,True,table2TransformationData,"",False
            except Exception as ex:
                print(ex)
                raise PreventUpdate()
    elif "columnTransformationDataDetails" in storeData.keys():
        # Reset the page level data store
        table2TransformationData = {}
        for row in storeData["columnTransformationDataDetails"]:
            if row["FileIdentifier"] not in table2TransformationData.keys():
                table2TransformationData[row["FileIdentifier"]] = {}
            table2TransformationData[row["FileIdentifier"]][row["ColumnName"]] = row["Transformations"]
        return "",False,table2TransformationData,"",True
    else : 
        raise PreventUpdate()


@app.callback(Output("saveTransformationModalBody","children"),
            Output("saveTransformationModal","is_open"),
            Output("transformationStore","data"), 
            Output("table1LoadingOutput","children"),
            
    [Input('saveTransform', 'n_clicks'),Input('data', 'children'),Input("saveTransformationModalClose", "n_clicks")],
    State('addTransformTable','data'),
    State("transformationStore","data"),State('experimentStore','data')
    )
def saveTransforTable1(n_clicks,inp1,closeClicks,data,transformationStore,storeData):
    if closeClicks > 0 and ctx.triggered_id == "saveTransformationModalClose":
        return "",False,dash.no_update, dash.no_update
    if n_clicks > 0 :
        if len(data) > 0:
            fileIdentifier = data[0]["FileIdentifier"]
            if len(transformationStore) == 0:
                transformationStore = {}
            transformationStore[fileIdentifier] = json.dumps(data)
            try:
                # Delete all records in database
                dboperations.executeStoredProcedure(DELETE_TRANSFORMATION_DETAILS_SP,"@ExperimentSetID = ?, @FileIdentifier=? ",(storeData["experimentsetid"],fileIdentifier),"dbo",0)

                inputDict = json.dumps(data)
                # Save forecast details to database
                dboperations.executeStoredProcedure(SAVE_TRANSFORMATION_DETAILS_SP ,"@ExperimentSetID = ? ,@FileIdentifier=?,@Transformations = ?",(storeData["experimentsetid"],fileIdentifier, inputDict),"dbo",0)
                
                print("Saved transformation data information!")
                return DATA_SAVE_MESSAGE,True,transformationStore,""
            except Exception as ex:
                print(ex)
                raise PreventUpdate()
    elif "transformationDataDetails" in storeData.keys():
        if len(transformationStore) == 0:
                transformationStore = {}
        for row in storeData["transformationDataDetails"]:
            transformationStore[row["FileIdentifier"]] = row["Transformations"]
        return "",False,transformationStore,""
    else : 
        raise PreventUpdate()


@app.callback(
    Output('addTransformListToTable','data'),
    Output("columnTransformValidationModalBody","children"),
    Output("columnTransformValidationModal","is_open"),
    Output('saveColumnTransformations',"disabled"),
    Input("addTransformTable",'active_cell'), # Table 2
    Input('addTransformListBtn', 'n_clicks'), # Add more button for table 2
    Input("timezoneConversionTable",'active_cell'), # Table 1 active cell data
    Input("columnTransformValidationModalClose", "n_clicks"),
    State('addTransformTable', 'data'), # file type , file identifier , column name from table 2
    State('addTransformListToTable','data'), # State of the Table 3
    State('transformDropdown','value'),
    State('operatorDropdown','value'),
    State('transformValue','value'),
    State('table2TransformationStore','data'),
    State('experimentStore','data')
    )
def TZtable(active,addClick,tztableClick,closeClicks,activeData,transformData,transformDropdown,operatorDropdown,transformValue,table2TransformationStore,storeData):
    if closeClicks > 0 and ctx.triggered_id == "columnTransformValidationModalClose":
        return "",False,dash.no_update, dash.no_update
    triggered_id = ctx.triggered_id
    global ColumnName
    validateMessage = ''
    saveButtonDisabled = True
    modalOpen = False
    df = pd.DataFrame(activeData)
    FileType = df.iloc[active['row'],:]['FileType']
    FileIdentifier =  df.iloc[active['row'],:]['FileIdentifier']
    ColumnName =  df.iloc[active['row'],:]['ColumnName']
    TagName =  df.iloc[active['row'],:]['ColumnTag']
    applyTransformFlag =  df.iloc[active['row'],:]['ApplyTransformFlag']

    if active is not None or addClick > 0 or tztableClick  is not None: 
        if transformData is None : 
            transformData = []
            rows = []
        if triggered_id == 'addTransformTable' :
            
            # Check if the data already exists in cache, read it and update that
            if table2TransformationStore is not None and len(table2TransformationStore) > 0 and FileIdentifier in table2TransformationStore.keys() and ColumnName in table2TransformationStore[FileIdentifier].keys():
                rows = json.loads(table2TransformationStore[FileIdentifier][ColumnName])
            elif applyTransformFlag == 'Yes' :
                transformDataDF = pd.DataFrame(transformData)
                # Check if the column is already present in the transformData grid
                if len(transformDataDF) > 0 and len(transformDataDF[(transformDataDF['FileIdentifier'] == FileIdentifier) & (transformDataDF['ColumnName'] == ColumnName) ]) >0 :
                    validateMessage =  "File Identifier and Column Combination Already populated"
                    rows = transformData 
                    modalOpen = True
                else : 
                    # Create all transformations default rows if flag is selected
                    allTransforms = []
                    expDetails =getdata.getExperimentDetails(storeData)
                    pt = PrepopulateTransformations(cleanedDF, "SCADA", EntityType, capacity=siteCapacity)
                    prepopulateValues = pt.get_list_transforms(ColumnName, TagName) 
                    lst = prepopulateValues[ColumnName]
                    for i in lst:
                        prepopulateValue = {"FileType": FileType,"FileIdentifier": FileIdentifier,'ColumnName' : ColumnName ,"TransformationType": i['transformation'],'Operator' : i['operator'],'TransformationValue' :i['transformValue']}
                        allTransforms.append(prepopulateValue)

                    transform_list = ["filter","scale"] 
                    for i in transform_list:
                        x = {"FileType": FileType,"FileIdentifier": FileIdentifier,'ColumnName' : ColumnName ,"TransformationType": f'{i}','Operator' : '','TransformationValue' :''}
                        allTransforms.append(x)
                        rows = allTransforms
            elif applyTransformFlag == 'No' :
                    rows = []
            if len(rows) > 0:
                saveButtonDisabled = False
            return rows,validateMessage,modalOpen,saveButtonDisabled
        elif triggered_id == 'addTransformListBtn' : # If add more button is clicked
            # TODO: Add validations for transformation, or which multiple entries should not be supported
            # Add row for the selections from drop down in grid
            if operatorDropdown is None or transformValue is None :
                validateMessage =  "All Fields Are Mandatory"
                return transformData,validateMessage,True,True
            x = {"FileType": FileType,"FileIdentifier": FileIdentifier,'ColumnName' : ColumnName ,"TransformationType": transformDropdown,'Operator' : operatorDropdown,'TransformationValue' :transformValue}
            transformData.append(x)
            return transformData,validateMessage,False,False
        elif triggered_id == 'timezoneConversionTable':
            return [],validateMessage,False,True
    else :
        raise PreventUpdate()

# Returns Future or entity related Datetime column tag elements
@app.callback(
    Output('FileIdentifier','options'),Output('futureCovComponents','children'),
    Input("FileType",'value'), State('sourceData','data'))
def filetypeBasedTags(value, sourceData):
    if value is not None:
        _,filenames_options = srcFileToDF(value,sourceData["data"])
        if value == 'FutureCovariates':
            datetimeComponents = html.Div([
                            dbc.Row([  
                                    dropdownTags('Select Available DateTime Columns','selectAvailDatetimeDropdown',3),
                                    dropdownTags('Available TimeZone Type','checkAvailDatetimeTypeDropdown',3),
                                    dropdownTags('Available TZaware Check','availDatetimeConversion',3),
                                    dbc.Col([html.Div(id = 'availTZConversion')],width = 3)
                            ]),
                            dbc.Row([  
                                    dropdownTags('Select Applicable DateTime Columns','selectApplDatetimeDropdown',3),
                                    dropdownTags('Applicable TimeZone Type','checkApplDatetimeTypeDropdown',3),
                                    dropdownTags('Applicable TZaware Check','applDatetimeConversion',3),
                                    dbc.Col([html.Div(id = 'applTZConversion')],width = 3)
                            ])
                            ])
        else : 
            datetimeComponents = html.Div([
                            dbc.Row([  
                                    dropdownTags('Select DateTime Columns','selectDatetimeDropdown',3),
                                    dropdownTags('TimeZone Type','checkDatetimeTypeDropdown',3),
                                    dropdownTags('DateTime TZaware Check','dateTimeConversion',3),
                                    dbc.Col([html.Div(id = 'TZConversion')],width = 3)
                            ])                     
                            ])
        return filenames_options,datetimeComponents
    else:
        raise PreventUpdate()

@app.callback(
     [
    Output('addTransformTable', 'data'),
    Output('edaColListDropdown','options'),
    Output('colListDropdown','options'),
    Output('saveTransform','disabled'),
    Output('activecellStore','data'),
    Output('resampleDropdown','options'),
    Output("transformationValidationModalBody","children"),
    Output("transformationValidationModal","is_open")],
    Input("timezoneConversionTable",'active_cell'),
    Input("addtransformBtn1",'n_clicks'),
    Input("transformationValidationModalClose", "n_clicks"),
    State('timezoneConversionTable', 'data'),
    State('colListDropdown','value'),
    State('ColumnTag','value'),
    State('resampleDropdown','value'),
    State('interpolateClass','value'),
    State('interpolateMethod','value'),
    State('applytransformDropdown','value'),
    State('sourceData','data'),
    State('experimentStore','data'),
    State('addTransformTable', 'data'),
    State("transformationStore","data")
    )
def TZtable(active,addclick,closeClicks,data,column,tag,resample,interpolateClass,interpolateMethod,allTransformFlag,sourceData,storeData,transformTable,transformationStore):
    validateMessage = ''
    if closeClicks > 0 and ctx.triggered_id == "transformationValidationModalClose":
        return dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,"",False
    if data is not None : 
        if transformTable is None : 
            transformTable = []
        global FileIdentifier,DateTime,DateTimeColumnName
        global cleanedDF
        df = pd.DataFrame(data)
        FileType = df.iloc[active['row'],:]['FileType']
        FileName =  df.iloc[active['row'],:]['FileName']
        DateTimeColumnName =  df.iloc[active['row'],:]['DateTimeColumnName']
        AvailColumnName =  df.iloc[active['row'],:]['AvailColumnName']
        FileIdentifier =  df.iloc[active['row'],:]['FileIdentifier']
        triggerId = ctx.triggered_id
        experimentSetName = storeData["experimentsetname"]
        DateTime = DateTimeColumnName
        path = f'{experimentSetName}/{TIMEZONE_CLEANED_FOLDER}'
        fullPath = f'{MASTER_FOLDER}/{path}/{FileName}'
        if not os.path.exists(fullPath):
            if not os.path.exists(f'{MASTER_FOLDER}/{path}/'):
                os.makedirs(f'{MASTER_FOLDER}/{path}/')
            # Download from blob
            blobOperations.downloadBlob(f'{path}/{FileName}',MASTER_FOLDER+"/")
        cleanedDF = pd.read_csv(fullPath,parse_dates=True)
        options = listToOptions([i for i in cleanedDF.columns if i not in [DateTimeColumnName,AvailColumnName,'Year', 'Month', 'Date']] )
        if triggerId == 'timezoneConversionTable' :
            if len(transformationStore) > 0  and FileIdentifier in transformationStore.keys():
                transformData = json.loads(transformationStore[FileIdentifier])
            else:
                transformData = []
            return [transformData,options,options,False,active,resample_options,validateMessage,False]
        elif triggerId == 'addtransformBtn1' :
            storeDataDF = getdata.getForecastSetupDetails(storeData)
            FileDetails = str(storeDataDF.to_dict(orient='records'))
            dataDF = pd.DataFrame(transformTable)
            if len(dataDF) > 0 and len(dataDF[(dataDF['FileIdentifier'] == FileIdentifier) & (dataDF['ColumnName'] == column) ]) >0 :
                validateMessage =  "File Identifier and Column Combination Already Exists"
                return transformTable,options,options,False,active,resample_options,validateMessage,True
            if tag is None or resample is None  or interpolateClass is None or interpolateMethod is None or allTransformFlag is None :
                validateMessage =  "All Fields are mandatory"
                return transformTable,options,options,False,active,resample_options,validateMessage,True

            row = {"FileType": FileType,"FileIdentifier": FileIdentifier,'FileDetails' : FileDetails,'ColumnName' :column, 'ColumnTag' :tag,'Resampler':resample,'InterpolationClass' :interpolateClass ,'InterpolationMethod' : interpolateMethod, 'ApplyTransformFlag' : allTransformFlag  }
            transformTable.append(row)
            return  [transformTable,options,options,False,active,resample_options,validateMessage,False]
    else : 
        raise PreventUpdate()

# if entity or past then create json  and call fixtime class to convert timeformat columnsd

def duplicateFileCheck(rows,FileName):
    FileList = [rows[i]['FileName'] for i in range(len(rows))]
    if FileName in FileList :
        return True
    return False


@app.callback(
    Output('OperatorTag','children'),
    Input('transformDropdown','value'))
def tzConversion(value):
    if value is None : 
        return dbc.Col([ 
                        html.Label('Actual Value'),
                        dcc.Input( id = 'operatorDropdown',type = 'text',style = {'width': '100%'})
                    ])
    if value is not None :
        if value in ['lower_capping','upper_capping','replace']:
            return dbc.Col([ 
                        html.Label('Actual Value'),
                        dcc.Input( id = 'operatorDropdown',type = 'text',style = {'width': '100%'})
                    ])
        elif value == 'scale':
            return dbc.Col([
                                html.Label('Operator'),
                                dcc.Dropdown(id = 'operatorDropdown',options = listToOptions(['Multiply','Divide','Add','Subtract']))
                            ])
        elif value == 'filter':
            return dbc.Col([
                                html.Label('Operator'),
                                dcc.Dropdown(id = 'operatorDropdown',options = listToOptions(['In' , 'Not In']))
                            ])
    else :
        raise PreventUpdate()
            

@app.callback(
    Output("timezoneValidationModalBody","children"),
    Output("timezoneValidationModal","is_open"),

    Output('applytransformDropdown','options'),
    Output('timezoneConversionTable','data'),
    Output('timezoneDetailsLoadingOutput',"children"),
    Output('saveTimezoneButton','disabled'),

    [Input("convertTimeButton",'n_clicks'), Input('data', 'children'),Input("timezoneValidationModalClose", "n_clicks")],

    [State("FileType",'value'),  
    State("FileIdentifier",'value'),
    State('experimentStore','data'),
    State("selectDatetimeDropdownStore",'data'),
    State("checkDatetimeTypeDropdownStore",'data'),
    State("dateTimeConversionStore",'data'),
    State("TZConversionDropdownStore",'data'),
    State("selectApplDatetimeDropdownStore",'data'),
    State("checkApplDatetimeTypeDropdownStore",'data'),
    State("applDatetimeConversionStore",'data'),
    State("applTZConversionDropdownStore",'data'),
    State("selectAvailDatetimeDropdownStore",'data'),
    State("checkAvailDatetimeTypeDropdownStore",'data'),
    State("availDatetimeConversionStore",'data'),
    State("AvailTZConversionDropdownStore",'data'),
    State('timezoneConversionTable', 'data'),
    State('timezoneConversionTable', 'columns'),
    State('sourceData', 'data')]
    )
def tzConversion(clicks,inp1,closeClicks,FileType,FileIdentifierValue ,storeData,selectDatetimeDropdownStore,checkDatetimeTypeDropdownStore,dateTimeConversionStore,TZConversionDropdownStore,selectApplDatetimeDropdownStore,checkApplDatetimeTypeDropdownStore,applDatetimeConversionStore,applTZConversionDropdownStore,selectAvailDatetimeDropdownStore,checkAvailDatetimeTypeDropdownStore,availDatetimeConversionStore,AvailTZConversionDropdownStore,tzdata,tzcolumns,sourceData):
    if closeClicks > 0 and ctx.triggered_id == "timezoneValidationModalClose":
        return "",False,dash.no_update, dash.no_update,dash.no_update,dash.no_update
    if clicks > 0:
        if FileType is None or FileIdentifierValue is None  :
            validateMessage =  "All Fields are mandatory"
            return validateMessage,True,apply_transform_flag_options,tzdata,"",dash.no_update
        sourceDataDF = pd.DataFrame(sourceData['data'])
        sourceDataDF = sourceDataDF[sourceDataDF['FileIdentifier'] == FileIdentifierValue ]
        FileName = sourceDataDF['BlobName'].values[0]
        global cleanedDF,datetimeCols,blobColumns
        if tzdata is None : 
            tzdata = []
        if duplicateFileCheck(tzdata,FileName) :
            validateMessage =  "File is already selected for conversion"
            return validateMessage,True,apply_transform_flag_options,tzdata,"",dash.no_update
        df,_ = srcFileToDF(FileType,sourceData["data"])
        df1 = df[df['BlobName'] ==  FileName].copy()
        AccountName = df1['AccountName'].values[0]
        ContainerName = df1['ContainerName'].values[0]
        BlobName = df1['BlobName'].values[0]
        _,df,blobColumns = blobOperations.getBlobDf(AccountName,ContainerName,BlobName)

        forecastDetails = getdata.getForecastSetupDetails(storeData)
        forecastTZ = forecastDetails['TimeZone'].unique()[0]

        # Timezone conversion started
        if FileType != 'FutureCovariates' :
            cleanedDF = getDF(forecastTZ,df,FileType,selectDatetimeDropdownStore ,checkDatetimeTypeDropdownStore,dateTimeConversionStore,TZConversionDropdownStore)
            datetimeCols = selectDatetimeDropdownStore
            tzdata.append({"FileIdentifier" : FileIdentifierValue,"FileType":FileType,"FileName": FileName,"DateTimeColumnName": selectDatetimeDropdownStore,'DateTimeTZType' : checkDatetimeTypeDropdownStore,'DateTimeTZAware':dateTimeConversionStore,'DateTimeTZConversionUnit' : TZConversionDropdownStore,
            "AvailColumnName": '','AvailTZType' : '','AvailTZAware':'','AvailTZConversionUnit' : ''  })
        else : 
            cleanedDF = getDF(forecastTZ,df,FileType,selectApplDatetimeDropdownStore,checkApplDatetimeTypeDropdownStore,applDatetimeConversionStore,applTZConversionDropdownStore,
                        selectAvailDatetimeDropdownStore,checkAvailDatetimeTypeDropdownStore,availDatetimeConversionStore,AvailTZConversionDropdownStore)
            datetimeCols = [ selectApplDatetimeDropdownStore,selectAvailDatetimeDropdownStore]
            row = {"FileIdentifier" : FileIdentifierValue,"FileType":FileType,"FileName": FileName,"DateTimeColumnName": selectApplDatetimeDropdownStore,'DateTimeTZType' : checkApplDatetimeTypeDropdownStore,'DateTimeTZAware': applDatetimeConversionStore,'DateTimeTZConversionUnit' : applTZConversionDropdownStore, 
            "AvailColumnName": selectAvailDatetimeDropdownStore,'AvailTZType' : checkAvailDatetimeTypeDropdownStore,'AvailTZAware':availDatetimeConversionStore,'AvailTZConversionUnit' : AvailTZConversionDropdownStore}
            tzdata.append(row)

        # Save the timezone converted file
        experimentSetName = storeData["experimentsetname"]
        path = f'{MASTER_FOLDER}/{experimentSetName}/{TIMEZONE_CLEANED_FOLDER}'
        fullPath = f'{path}/{FileName}'
        if not os.path.exists(path):
            os.makedirs(path)
        cleanedDF.to_csv(fullPath,index = None)
        
        try : 
            blobOperations.uploadBlob(fullPath)
        except Exception as e:
            # Raise exception here...testing the uploading 
            validateMessage = 'Error while uploading files'
        validateMessage = 'Conversion Completed'
        popupState = True
    elif "timezoneDataDetails" in storeData.keys():
        tzdata = storeData["timezoneDataDetails"]
        validateMessage = ""
        popupState = False
    else:
        raise PreventUpdate() 
    return validateMessage, popupState ,apply_transform_flag_options,tzdata, "", False
    
# Create new tag element if the datetime zone type is standard or timezone
@app.callback(
    Output('TZConversion','children'),
    Output('dateTimeConversionStore','data'),
    Input("dateTimeConversion",'value') ,
    State("checkDatetimeTypeDropdown",'value')
    )
def getTZConversionTagDateTime(value1,value2):
    if value1 is not None :
        if value2 == 'Standard' :
            return dbc.Col([
                                html.Label('TZConversion'),
                                dcc.Dropdown(id = 'TZConversionDropdown',options = listToOptions(timezoneDf['UTC'].unique()))
                            ]),value1
        elif  value2 == 'Timezone' :
            return dbc.Col([
                                html.Label('TZConversion'),
                                dcc.Dropdown(id = 'TZConversionDropdown',options = listToOptions(timezoneDf['TimeZone'].unique()))
                            ]),value1
        elif  value2 == 'UnixTime' :
            return "",value1
        elif  value2 == 'Local' :
            return dbc.Col([
                                html.Label('TZConversion'),
                                dcc.Dropdown(id = 'TZConversionDropdown',options = listToOptions([targetTimezone]))
                            ]),value1
    else:
        raise PreventUpdate()

@app.callback(
    Output('availTZConversion','children'),
    Output('availDatetimeConversionStore','data'),
    Input("availDatetimeConversion",'value') ,
    State("checkAvailDatetimeTypeDropdown",'value')
    )
def getTZConversionTagAvailDateTime(value1,value2):
    if value1 is not None :
        if value2 == 'Standard' :
            return dbc.Col([
                                html.Label('TZConversion'),
                                dcc.Dropdown(id = 'AvailTZConversionDropdown',options = listToOptions(timezoneDf['UTC'].unique()))
                            ]),value1
        elif  value2 == 'Timezone' :
            return dbc.Col([
                                html.Label('TZConversion'),
                                dcc.Dropdown(id = 'AvailTZConversionDropdown',options = listToOptions(timezoneDf['TimeZone'].unique()))
                            ]),value1
        elif  value2 == 'Local' :
            return dbc.Col([
                                html.Label('TZConversion'),
                                dcc.Dropdown(id = 'AvailTZConversionDropdown',options = listToOptions([targetTimezone]))
                            ]),value1
        elif  value2 == 'UnixTime' :
            return "",value1
        
    else:
        raise PreventUpdate()

@app.callback(
    Output('applTZConversion','children'),
    Output('applDatetimeConversionStore','data'),
    Input("applDatetimeConversion",'value') ,
    State("checkApplDatetimeTypeDropdown",'value')
    )
def getTZConversionTagAppllDateTime(value1,value2):
    if value1 is not None :
        if value2 == 'Standard' :
            return dbc.Col([
                                html.Label('TZConversion'),
                                dcc.Dropdown(id = 'applTZConversionDropdown',options = listToOptions(timezoneDf['UTC'].unique()))
                            ]),value1
        elif  value2 == 'Timezone' :
            return dbc.Col([
                                html.Label('TZConversion'),
                                dcc.Dropdown(id = 'applTZConversionDropdown',options = listToOptions(timezoneDf['TimeZone'].unique()))
                            ]),value1
        elif  value2 == 'Local' :
            return dbc.Col([
                                html.Label('TZConversion'),
                                dcc.Dropdown(id = 'applTZConversionDropdown',options = listToOptions([targetTimezone]))
                            ]),value1
        elif  value2 == 'UnixTime' :
            return "",value1

    else:
        raise PreventUpdate()

#START
@app.callback(
    Output('TZConversionDropdownStore','data'),
    Input("TZConversionDropdown",'value') 
    )
def entityStore(TZConversionDropdown):
    if TZConversionDropdown is not None : 
        return TZConversionDropdown

@app.callback(
    Output('selectDatetimeDropdownStore','data'),
    Input("selectDatetimeDropdown",'value') 
    )
def entityStore(selectDatetimeDropdown):
    if selectDatetimeDropdown is not None : 
        return selectDatetimeDropdown

       
@app.callback(
    Output('selectApplDatetimeDropdownStore','data'),
    Input("selectApplDatetimeDropdown",'value') 
    )
def entityStore(selectApplDatetimeDropdown):
    if selectApplDatetimeDropdown is not None : 
        return selectApplDatetimeDropdown

@app.callback(
    Output('applTZConversionDropdownStore','data'),
    Input("applTZConversionDropdown",'value') 
    )
def entityStore(applTZConversionDropdown):
    if applTZConversionDropdown is not None : 
        return applTZConversionDropdown

  
@app.callback(
    Output('selectAvailDatetimeDropdownStore','data'),
    Input("selectAvailDatetimeDropdown",'value') 
    )
def entityStore(selectAvailDatetimeDropdown):
    if selectAvailDatetimeDropdown is not None : 
        return selectAvailDatetimeDropdown

@app.callback(
    Output('AvailTZConversionDropdownStore','data'),
    Input("AvailTZConversionDropdown",'value') 
    )
def entityStore(AvailTZConversionDropdown):
    if AvailTZConversionDropdown is not None : 
        return AvailTZConversionDropdown

# enable eda button only if more than 1 column is selected
@app.callback(
    [Output('edaButton','disabled'),
    Output('vizTypeDropdown','options'),
    Output('vizTypeDropdown','disabled')],
    Input("edaColListDropdown",'value'))
def enableEDAVizButtons(value):
    if value is not None : 
        if len(value) > 0 :
            return [False,viz_options,False]
        else:
            return [True,viz_options,True]
    else:
        return [True,viz_options,True]

def step(cleanedDF, Col,graphname):
    up = UnivariatePlotly(cleanedDF, Col,'DateTime',['Year','Month'])
    fig = eval('up.'+graphname+'()')
    if graphname == 'boxplot_graph' :
        return html.Div([dcc.Graph(id = graphname,figure = fig['Year'],style={'width': '100vh', 'height': '50vh'}),
                        dcc.Graph(id = graphname,figure = fig['Month'],style={'width': '100vh', 'height': '50vh'}) ])
    else : 
        return dcc.Graph(id = graphname,figure = fig,style={'width': '150vh', 'height': '50vh'})


@app.callback(
    Output('graphComponent','children'), Output("graphLoadingOutput","children"),
    Input("edaButton",'n_clicks'),
    Input("convertTimeButton","n_clicks"),
    Input("addTransformTable",'active_cell'), 
    Input('timezoneConversionTable', 'active_cell'),
    State('vizTypeDropdown','value'),
    State("edaColListDropdown",'value')
    )
def sourcefiletable1(clicks,conv_clicks,activecell,TZactive,graphtype,Col):
    div_list = []
    if ctx.triggered_id == 'edaButton' :
        if clicks > 0 : 
            for graphname in graphtype:
                div_list += [  step(cleanedDF,Col,graphname)   ]
            return div_list,""
        else:
            raise PreventUpdate()
    elif ctx.triggered_id == 'convertTimeButton'  :
        return html.Div([ html.Label('') ]) ,""
    elif ctx.triggered_id == 'addTransformTable' :
        if activecell is not None : 
            return html.Div([ html.Label('') ]) ,""
    elif ctx.triggered_id == 'timezoneConversionTable' :
        if TZactive is not None : 
            return html.Div([ html.Label('') ]) ,""
    else : 
        raise PreventUpdate()


# select DateTime and DateTime type Columns from all columns dropdown
@app.callback(
    Output('selectDatetimeDropdown','options'),
    Output('checkDatetimeTypeDropdown','options'),Output("fileLoadingOutput","children"),
    Input("FileIdentifier",'value'),  
    State("FileType",'value') ,
    State('sourceData', 'data'))
def sourcefiletable1(FileIdentifier,FileType,sourceData):
    if(FileIdentifier is not None):
        if FileType == 'Entity' or FileType == 'PastCovariates' :
            FileName = getFileName(FileIdentifier,sourceData['data'])
            _,colListOptions = getColList(FileType,FileName,sourceData["data"])
            return colListOptions,timezoneTypeOptions, ""
    else:
        raise PreventUpdate()

# Applicable and Available DateTime and Datetime Type Columns dropdowns
@app.callback(
    Output('selectApplDatetimeDropdown','options'),
    Output('selectAvailDatetimeDropdown','options'),
    Output('checkAvailDatetimeTypeDropdown','options'),
    Output('checkApplDatetimeTypeDropdown','options'),
    Output("fileFutureCovLoadingOutput","children"),
    Input("FileIdentifier",'value'),  
    State("FileType",'value'),
    State('sourceData', 'data'))
def sourcefiletable2(FileIdentifier,FileType,sourceData):
    if FileType == 'FutureCovariates' :
        FileName = getFileName(FileIdentifier,sourceData['data'])
        _,colListOptions = getColList(FileType,FileName,sourceData["data"])
        return colListOptions,colListOptions,timezoneTypeOptions,timezoneTypeOptions, ""

# Based on DateTime Type dropdown fill tz aware dropdown or fill unix conversion units
@app.callback(
    Output('dateTimeConversion','options'),
    Output("checkDatetimeTypeDropdownStore",'data') ,
    Input("checkDatetimeTypeDropdown",'value') )
def getdateTimeConversion(value):
    if value is not None:
        return returnOptions(value),value
    else:
        raise PreventUpdate()

@app.callback(
    Output('applDatetimeConversion','options'),
    Output("checkApplDatetimeTypeDropdownStore",'data') ,
    Input("checkApplDatetimeTypeDropdown",'value') )
def getapplDatetimeConversion(value):
    if value is not None:
        return returnOptions(value),value
    else:
        raise PreventUpdate()

@app.callback(
    Output('availDatetimeConversion','options'),
    Output("checkAvailDatetimeTypeDropdownStore",'data') ,
    Input("checkAvailDatetimeTypeDropdown",'value') )
def getavailDatetimeConversion(value):
    if value is not None:
        return returnOptions(value),value
    else:
        raise PreventUpdate()

@app.callback(
    Output('transformListDropdown','options'),
    Input("colListDropdown",'value') )
def gettransformListDropdown(value):
    if value is not None and len(value) > 0 :
        return transform_options
    else:
        raise PreventUpdate()

# page load method
@app.callback(Output('sourceData','data'),
             Output('ColumnTag','options'), 
             Output('interpolateClass','options'), 
             Output('granularityStore','data')  ,
             Output('transformDropdown','options'),
             Output('entitytype','data'),
                [Input('data', 'children')],
              State('experimentStore','data'),
              State('sourceData','data'),
              )
def onTabLoad(inp1, data,srcdata):
    global siteCapacity,granularity,targetTimezone,EntityType,targetTimezoneMergeFile
    print("Executing tab 4 page load")
    sourceData = getdata.getSourceDataDetails(data)
    EntityTypeList = getdata.getEntityType(data)
    EntityType = EntityTypeList[0]['EntityType']
    expDetails =getdata.getExperimentDetails(data)
    storeDataValue = getdata.getForecastSetupDetails(data)
    granularity = str(storeDataValue.iloc[0,:]['Granularity'])+storeDataValue.iloc[0,:]['GranularityUnits']
    targetTimezoneMergeFile = str(storeDataValue.iloc[0,:]['TimeZone'])
    #granularity = '1H' # TODO : check with Srini
    print('on load granulairty check ',granularity)
    if EntityType == 'wind' :
        siteCapacity = expDetails['SiteCapacity']
    elif EntityType == 'solar' : 
        siteCapacity = expDetails['overallcapacity']
    else :
        siteCapacity = None
    targetTimezone = str(storeDataValue.iloc[0,:]['TimeZone'])
    pt = PrepopulateTransformations({}, "SCADA", EntityType, capacity=siteCapacity)
    columnOptions = listToOptions(pt.accepted_tags)
    return {"data" : sourceData.to_dict("records") } , columnOptions , interpolateClassOptions,granularity,transform_options,EntityType

# Timezone: Convert and Save Button saveTZModal
@app.callback( Output("timezoneDetailsSaveLoading","children"),
                Output("saveTZModalBody","children"),
                Output("saveTZModal","is_open"),
    Input('saveTimezoneButton', 'n_clicks'),Input('data', 'children'),Input("saveTZModalClose", "n_clicks"),
    [State('timezoneConversionTable', 'data'),State('experimentStore','data')]
)
def saveTimezone(clicks,inp1,closeClicks,timezoneData,data):
    if closeClicks > 0 and ctx.triggered_id == "saveTZModalClose":
        return "","",False
    if clicks > 0:
        try:
            # Delete all records in database
            dboperations.executeStoredProcedure(DELETE_TIMEZONE_DETAILS_SP,"@ExperimentSetID = ? ",(data["experimentsetid"]),"dbo",0)
            
            # Save timezone details to database
            dboperations.executeStoredProcedure(SAVE_TIMEZONE_DETAILS_SP ,"@ExperimentSetID = ? ,@TimeZoneDetails=?",(data["experimentsetid"], json.dumps(timezoneData)),"dbo",0)
            
            print("Saved timezone data information!")

            return "",DATA_SAVE_MESSAGE,True
        except Exception as ex:
            print(ex)
            raise PreventUpdate()
    else:
        raise PreventUpdate()

# Transform and Save Button
@app.callback( Output('tab-5','disabled'),
         Output("transformationLoadingOutput","children"),
         Output("transformActionModalBody","children"),
        Output("transformActionModal","is_open"),
    Input('transformActionButton', 'n_clicks'),
    Input('data', 'children'),
    Input('addTransformListToTable', 'data'),
    Input("transformActionModalClose", "n_clicks"),
    [State('addTransformListToTable', 'data'),
    State('experimentStore','data'),
    State('sourceData','data') ,
     State('timezoneConversionTable', 'data'),
     State('addTransformTable', 'data'),
      State('timezoneConversionTable', 'active_cell'),
      State('granularityStore','data')
     ]
)
def transformAndSave(clicks,inp1,transformDataTable,closeClicks,transformationData,data,sourceData,TZdata,TRANSdata,TZactive,granularity):
    if closeClicks > 0 and ctx.triggered_id == "transformActionModalClose":
        return dash.no_update, dash.no_update,"",False
    if clicks > 0:
        if transformDataTable is not None:

            # Read timezone conversion rules
            TZdata = getdata.getTimezoneDetails(data) 
            TZdata = pd.DataFrame(TZdata)
            # Read time zone information
            TZDateTime = TZdata.iloc[TZactive['row'],:]['DateTimeColumnName']
            TZAvilTime = TZdata.iloc[TZactive['row'],:]['AvailColumnName']
            FileName = TZdata.iloc[TZactive['row'],:]['FileName']
            FileTypeValue = TZdata.iloc[TZactive['row'],:]['FileType']
            FileIdentifier = TZdata.iloc[TZactive['row'],:]['FileIdentifier']

            experimentSetName = data["experimentsetname"]
            path = f'{experimentSetName}/{TIMEZONE_CLEANED_FOLDER}'
            fullPath = f'{MASTER_FOLDER}/{path}/{FileName}'
            tzcleanedDF = pd.read_csv(fullPath,parse_dates=True)
            # Convert to target timezone
            tzcleanedDF[TZDateTime] = pd.to_datetime(tzcleanedDF[TZDateTime], utc=True).map(lambda x: x.tz_convert(targetTimezoneMergeFile))

            transformedfile = performTransformations(data,TZDateTime,TZAvilTime,FileIdentifier,FileTypeValue, tzcleanedDF,granularity)

            path = f'{experimentSetName}/{TRANSFORM_CLEANED_FOLDER}'
            fullPath = f'{MASTER_FOLDER}/{path}'
            if not os.path.exists(fullPath):
                os.makedirs(fullPath)
            transformedfile.to_csv(os.path.join(fullPath,FileIdentifier+'.csv') ,index = None)
            blobOperations.uploadBlob(os.path.join(fullPath,FileIdentifier+'.csv'))
        else:
            #Upload data to blob (TZ Cleaned if there is no transformation)
            for row in sourceData["data"]:
                experimentSetName = data["experimentsetname"]
                path = f'{MASTER_FOLDER}/{TRANSFORM_CLEANED_FOLDER}/{experimentSetName}/'
                if not os.path.exists(path):
                    os.makedirs(path)
                FileName = row["BlobName"]
                try : 
                    shutil.copy(f'{MASTER_FOLDER}/{TIMEZONE_CLEANED_FOLDER}/{experimentSetName}/{FileName}',f'{path}/{FileName}')
                    blobOperations.uploadBlob(f'{path}/{FileName}')
                except Exception as e:
                    # Raise exception here...testing the uploading 
                    print('Error while uploading')

        return False, "",DATA_SAVE_MESSAGE,True
    elif "transformationDataDetails" in data.keys() or "timezoneDataDetails" in data.keys():
        return False, "","",False
    else:
        raise PreventUpdate()

def performTransformations(data,TZDateTime,TZAvilTime,FileIdentifier,FileTypeValue, tzcleanedDF, _granularity):
    # Read transformation rules 
    transData = getdata.getTransformationDetails(data)
    transcoldata = getdata.getColumnTransformationDetails(data)
    transData = pd.DataFrame(transData) #Transformation data for table 1
    transcoldata = pd.DataFrame(transcoldata) #Detailed Transformation data for table 2

    # Parse transformation data for the selected file
    transformdata = transData[transData['FileIdentifier']  == FileIdentifier ]['Transformations'].values
    transformdata = json.loads(transformdata[0])
    transformdata = pd.DataFrame(transformdata)
    columnTrans = {}

    ct = ColumnarTransformations.ColumnarTransformations()
    for j in range(len(transformdata)) :
        transformdatadf = transformdata.iloc[j,:]
        Resampler = transformdatadf['Resampler']
        Interpolation = transformdatadf['InterpolationMethod']
        ColumnName = transformdatadf['ColumnName']
        FileType = transformdatadf['FileType']
        transformcoldata = transcoldata[ (transcoldata['FileIdentifier']  == FileIdentifier ) & (transcoldata['ColumnName']  == ColumnName ) ]['Transformations'].values
        transformcoldata = json.loads(transformcoldata[0])
        transformcoldata = pd.DataFrame(transformcoldata)
        transformList = []
        for k in range(len(transformcoldata)) :
            transformcoldatadf = transformcoldata.iloc[k,:]
            transformList.append((transformcoldatadf['TransformationType'],transformcoldatadf['TransformationValue'],transformcoldatadf['Operator']))

        columnTrans[ColumnName] = {'transformations': transformList,'resample':Resampler, 'interpolation':Interpolation} 
    column_transform_operator_dict = {}
    column_transform_operator_dict["granularity"] = _granularity 
    
    if FileTypeValue =='FutureCovariates' :
        column_transform_operator_dict['file_details'] = {FileIdentifier:{'df':tzcleanedDF, 'file_type':FileType, 'date_time': TZDateTime,'forecast_time':TZAvilTime,'columns' : columnTrans}}
    else : 
        column_transform_operator_dict['file_details'] = {FileIdentifier:{'df':tzcleanedDF, 'file_type':FileType, 'date_time': TZDateTime,'columns' : columnTrans}}

    d = ct.perform_transformations(column_transform_operator_dict)
    
    transformedfile = d['file_details'][FileIdentifier]["transformed_df"] 
    transformedfile.rename(columns = { TZDateTime : 'DateTime'},inplace = True)

    return transformedfile

# Enable Add button callbacks
@app.callback( Output('addtransformBtn1','disabled'),
                Input('colListDropdown', 'value'),
                Input('ColumnTag', 'value'),
                Input('resampleDropdown', 'value'),
                Input('interpolateClass', 'value'),
                Input('interpolateMethod', 'value'),
                Input('applytransformDropdown', 'value'))
def enableAddTransformButton(colListDropdown,ColumnTag,resampleDropdown,interpolateClass,interpolateMethod,applytransformDropdown):
    if colListDropdown is not None or ColumnTag is not None or resampleDropdown is not None or interpolateClass is not None or  interpolateMethod is not None or applytransformDropdown is not None:
        return False
    else:
        raise PreventUpdate()

@app.callback( Output('addTransformListBtn','disabled'),
                Input('transformDropdown', 'value'),
                Input('transformValue', 'value'),
                Input('operatorDropdown', 'value'))
def enableAddTransformButton(transformDropdown,transformValue,operatorDropdown):
    if transformDropdown is not None or transformValue is not None or operatorDropdown is not None:
        return False
    else:
        raise PreventUpdate()
                




