#Copyright (c) Microsoft. All rights reserved.
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import sys
import gc
import bz2
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
from BuildModel import BuildModel
import pandas as pd
import logging
import numpy as np
import os
import time
from FeatureEngineeringUtils import *

import matplotlib.pyplot as plt
import tensorflow
from tensorflow.keras.models import load_model
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input

from deepmc import golive_train_modules
from deepmc import modelsv3_transformer
from deepmc import modelsvb
from deepmc import golive_test_modules

import pickle
import json
from json import JSONEncoder

from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler

from DeepMCPipeline import *

from dboperations.dboperations import executeStoredProcedure
from logUtils import get_AMLRunId, update_training_status, get_ChildAMLRunId
from tensorflowCallbacks import TensorflowTrainingLossDatabaseUpdateCallback
from logConfig import TRAINING_START, TRAINING_END

def __generateDates__(start,end,freq):
    dates = pd.to_datetime(pd.date_range(start = str(start) , end = str(end) ,freq =freq))
    return dates

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


class DeepMC(BuildModel):
    def __init__(self,params):
        super().__init__(params)
        print(self.modelName+" model initialized")
        self.Blockno = self.parameters["Blockno"]
        self.epochs = self.parameters.get("epochs")
        self.batch_size = self.parameters.get("batch_size")
        self.trunc = self.parameters.get("trunc")
        self.modelType = self.modelName 
        self.internalParams = self.parameters.get("internalParams")
        self.train_pipeline_config = params["train_pipeline_config"]
        self.isOptimizationEnabled = params["isOptimizationEnabled"]
        self.outputPath = self.modelPath
        self.__preprocessData__()
        self.quantilePrecList = self.parameters.get("quantileList")
        self.quantileList,self.lengthQuantileList,self.qunatiles,self.quantileNames = self.__quantileDetails__(self.quantilePrecList,self.parameters)
    
    def __quantileDetails__(self,quantilePrecList,par):
        quantileList = [i/100 for i in quantilePrecList]
        quantileNames  = [str('p'+str(i)) for i in quantilePrecList]
        lengthQuantileList = len(quantilePrecList)
        if lengthQuantileList == 0 :
            qunatiles = [0.5]
        else: 
            qunatiles = quantileList
        return quantileList,lengthQuantileList,qunatiles,quantileNames

    def __preprocessData__(self,isTrain=True):
        try:
            super().__preprocess__()
            # Load preprocessed data

            # Split the dataset
            self.__buildTrainTestDataSet__()

            trw_data_df = self.trw_data_df  

            tew_data_df = self.tew_data_df

            # Scale the train data set
            self.output_scaler = StandardScaler() 
            self.output_scaler.fit_transform(np.expand_dims(trw_data_df[self.targetColumn].values,axis=1))
        
            self.train_scaler = StandardScaler() 
            self.trw_data_df = pd.DataFrame(self.train_scaler.fit_transform(trw_data_df), columns=trw_data_df.columns,index=trw_data_df.index)
            # Scale the test data set
            self.tew_data_df = pd.DataFrame(self.train_scaler.transform(tew_data_df), columns=tew_data_df.columns,index=tew_data_df.index)

        except Exception as ex:
            logging.error("Error in preprocessing.")
            logging.error(ex)
            raise ex

    def __buildTrainTestDataSet__(self):
        
        self.data = self.data[self.data.index<=str(self.val_end)]
        
        train = self.data[self.data.index<=self.train_end]
        split = int(train.shape[0])  
        data_df = self.data[self.requiredColumns+[self.targetColumn]+self.futureCovariates]
        self.trw_data_df = data_df.iloc[:split]
        self.tew_data_df = data_df.iloc[split-self.trunc+self.horizon:]

    def __generateWavelets__(self):
        logging.info("Starting Wavelet generation")
        try:
            i=0
            start = i*self.trunc #trunc = chunk data
            end = start   
            n_pred_var = self.targetColumn  

            # Prepare wavelets for train dataset
            t_train_X = []
            t_train_y = []
            trw_data_df = self.trw_data_df

            std_dict ={}
            for col in trw_data_df.columns:
                std_dict[col] = trw_data_df[col].std()

            tew_data_df = self.tew_data_df

            # This loop will go till the length of training dataset and wavelet transformation is done just for length of trunc in one go
            while(end<trw_data_df.shape[0]):
                start = i
                end = start + self.trunc
                i=i+1
                data_df = trw_data_df.iloc[start:end]
                _, _, _, _,train_uX, train_uy = golive_train_modules.convert_df_wavelet_input(data_df,n_pred_var,True, self.lookback,self.horizon , 'bior3.5','periodic') 
                t_train_X.append(train_uX)
                t_train_y.append(train_uy)

            # Prepare wavelets for test dataset
            t_test_X = []
            t_test_y=[]
            i=0
            start = i
            end = start
            while(end<tew_data_df.shape[0]):  
                start = i
                end = start + self.trunc
                i=i+1
                data_df = tew_data_df.iloc[start:end]
                _, _, _, _, test_uX, test_uy = golive_train_modules.convert_df_wavelet_input(data_df,n_pred_var,True, self.lookback, self.horizon, 'bior3.5','periodic')
                t_test_X.append(test_uX)
                t_test_y.append(test_uy)
            
            # Merge Original and transformed dataset outputs
            train_X = t_train_X[0].copy()
            train_y = t_train_y[0].copy()
            for i in range(1,len(t_train_X)):
                train_y = np.append(train_y, t_train_y[i], axis=0)
                for j in range(len(t_train_X[i])):
                    train_X[j] = np.append(train_X[j], t_train_X[i][j], axis=0)

            test_X = t_test_X[0].copy()
            test_y = t_test_y[0].copy()
            for i in range(1,len(t_test_X)):
                test_y = np.append(test_y, t_test_y[i], axis=0)
                for j in range(len(t_test_X[i])):
                    test_X[j] = np.append(test_X[j], t_test_X[i][j], axis=0)
            
            # Save the preprocessing objects to pickle file
            try:
                filePath = self.__saveModel__([train_X, train_y, test_X, test_y, self.train_scaler,self.output_scaler, t_train_X, t_train_y, t_test_X, t_test_y,std_dict],self.modelType+"_train")
                self.preprocessObject = [train_X, train_y, test_X, test_y, self.train_scaler,self.output_scaler, t_train_X, t_train_y, t_test_X, t_test_y]
                uploadToDatastore(self.modelPath)
                self.train_X = train_X
                self.train_y = train_y
                self.test_X = test_X
                self.test_y = test_y
                self.t_train_X = t_train_X
                self.t_train_y = t_train_y
                self.t_test_X = t_test_X
                self.t_test_y = t_test_y
                logging.info("Wavelet generation completed")
            except Exception as e:
                logging.error(e)
                raise ex
        except Exception as ex:
            logging.error("Error in wavelet generation.")
            logging.error(ex)
            raise ex
    
    def trainModel(self):
        logging.info("=========Start: Model Training=========")
        #==================== Generate wavelets===========================
        self.__generateWavelets__()
        
        AMLRunId = get_AMLRunId(modelPath=self.outputPath)
        ChildAMLRunId = get_ChildAMLRunId(modelPath=self.outputPath)
        print("inspect.stack()[1][3]", inspect.stack()[1][3])
        if 'objective' not in inspect.stack()[1]:
            update_training_status(AMLRunId,TRAINING_START,None,-1,None,None,ChildAMLRunId,self.horizon)
        
        try:
            #==================== Training code===============================
            
            steps = []
            self.train_pipeline_config["outputFolderName"] = self.modelPath
            
            for pred_idx in range(0,self.horizon): 
                modelName = "model"+str(pred_idx)

                step = buildPipelineStep(modelName,self.train_pipeline_config,json.dumps(self.internalParams),pred_idx,self.horizon)
                steps.append(step)
            
            try:
                logging.info("Creating and submitting pipeline")
                buildPipeline(steps,self.train_pipeline_config)
            except Exception as ex:
                logging.error("Internal Pipeline run failed")
                raise ex
        
            logging.info("Pipeline completed")

            downloadModels(self.modelPath,self.modelType)
            print("Models downloaded")
            
            self.list_model=[]
            for pred_idx in range(self.horizon):
                print("Loading model: ", pred_idx)
                self.list_model.append(load_model(self.modelPath+self.modelType+'/model'+str(pred_idx)))
            
            logging.info("Model training completed")
        except Exception as ex:
            logging.error("Error in model training.")
            logging.error(ex)
            raise ex
            
        try:
            self.__postprocessing__()
        except Exception as ex:
            logging.error("Error in model post processing.")
            logging.error(ex)
            raise ex
        if 'objective' not in inspect.stack()[1]:
            update_training_status(AMLRunId,TRAINING_END,None,-1,None,None,ChildAMLRunId,self.horizon)

        return self.modelPath+"/"+self.modelType
        
    def __simple_mixture_model__(self):
        model = Sequential()
        model.add(Input(shape=(self.horizon,)))    
        model.add(Dense(self.lookback/2, activation='relu'))
        model.add(Dense(self.lookback, activation='relu'))
        model.add(Dense(self.horizon))
        model.compile(loss='mae', optimizer='adam')
        return model

    def __fit_model__(self,model, train_X, train_y, test_X, test_y,idx):
        batch_size = self.horizon-1
        validation_data = (test_X, test_y)
        params = self.modelType, self.modelPath
        # Check if the objective function is being called (i.e. if hyperparameter tuning is happening) if 'objective' is not inspect.stack()[1][3]
        # If not, add the database update callback callbacks.append(TensorflowTrainingLossDatabaseUpdateCallback(params)) 
        database_update_callbacks = []
        if 'objective' not in inspect.stack()[1]:
            # If not, add the database update callback
            database_update_callbacks.append(TensorflowTrainingLossDatabaseUpdateCallback(params,idx))    
        history = model.fit(train_X, train_y, epochs=self.epochs, batch_size=batch_size, validation_data=validation_data,verbose=1, callbacks=database_update_callbacks)
        return model
        
    def __postprocessing__(self):
        self.postModels = []
        #=========================Post processing Training code=====================
        y = self.test_y
        yhat = np.empty(y.shape)
        var_shape = self.horizon-1
        mix_yhat = np.empty([y.shape[0]-var_shape, y.shape[1], y.shape[1]]) #23
        mix_train_yhat = np.empty([self.train_y.shape[0]-var_shape, self.train_y.shape[1], self.train_y.shape[1]]) #23

        idx=0
        total_rmse = []
        mix_model_list=[]
        mix_train_yc = np.empty([self.train_y.shape[0]-var_shape, self.train_y.shape[1], self.train_y.shape[1]]) #23
        mix_yc = np.empty([y.shape[0]-var_shape, y.shape[1], y.shape[1]]) #23

        for model in self.list_model:
            print(idx)
            train_yhat = model.predict(self.train_X)[:,0,0]
            test_yhat = model.predict(self.test_X)[:,0,0]
            
            _,_,mix_train_X,_,_,_ = modelsvb.dl_preprocess_data(pd.DataFrame(train_yhat), ts_lookback=self.horizon, ts_lookahead=self.horizon, pred_var_idx=0,validation=False, training=False)

            _,_,mix_train_y,_,_,_ = modelsvb.dl_preprocess_data(pd.DataFrame(self.train_y[:,idx,0]), ts_lookback=self.horizon, ts_lookahead=self.horizon, pred_var_idx=0,validation=False, training=False)

            _,_,mix_test_X,_,_,_ = modelsvb.dl_preprocess_data(pd.DataFrame(test_yhat), ts_lookback=self.horizon, ts_lookahead=self.horizon, pred_var_idx=0,validation=False, training=False)

            _,_,mix_test_y,_,_,_ = modelsvb.dl_preprocess_data(pd.DataFrame(self.test_y[:,idx,0]), ts_lookback=self.horizon, ts_lookahead=self.horizon, pred_var_idx=0,validation=False, training=False)
            
            mix_model = self.__simple_mixture_model__()
            history = self.__fit_model__(mix_model, mix_train_X[:,:,0], mix_train_y[:,:,0], mix_test_X[:,:,0], mix_test_y[:,:,0],idx)
            mix_model_list.append(history)
            
            mix_model.save(self.modelPath+"/"+self.modelType+'/post_model_'+str(idx)+'.h5')
            self.postModels.append(mix_model)

            yhat[:,idx,0]=test_yhat
            mix_yhat[:,:,idx] = mix_model.predict(mix_test_X[:,:,0])
            mix_train_yhat[:,:,idx] = mix_model.predict(mix_train_X[:,:,0])
            
            mix_yc[:,:,idx] = mix_test_y[:,:,0]
            mix_train_yc[:,:,idx] = mix_train_y[:,:,0]
            
            idx=idx+1
        #==================================================================================
        
    def testModel(self):
        rmsescore = 0    
        try:
            data_df = self.data[self.requiredColumns+[self.targetColumn]+self.futureCovariates+[self.dateField+"Original"]]
            data_df = data_df[data_df.index<=str(self.val_end)]
            self.forecast_params["predDate"] = self.val_start
            self.predSeries = DeepMC.predict(self.forecast_params,data_df)  
            try:
                valResultParams = {
                    "train_end": self.train_end 
                    ,"val_start": self.val_start 
                    ,"val_end": self.val_end 
                    ,"isScore" : False
                    ,"targetColumn" : self.targetColumn
                    ,"dateField" : self.dateField
                    ,"frequency" : self.frequency
                    ,"frequency_duration" : self.frequency_duration
                    ,"multiplicationFactor": self.multiplicationFactor
                    ,"horizon" : self.horizon
                    ,"filePath" : self.modelPath+self.modelType
                    ,"modelType" : self.modelType
                    ,"quantileList" : self.quantileList
                }
                outputData = DeepMC.prepareValResults(self.predSeries,data_df,valResultParams)
                uploadToDatastoreWithTargetPath("validate",self.modelPath+self.modelType)
            except Exception as ex:
                print("Error in preparing validation results")
                print(ex)
                raise ex
                
        except Exception as ex:
            logging.error("Error in model evaluation.")
            logging.error(ex)
            raise ex

        try:
            rmsescore = self.__rmse__(outputData)
            print(rmsescore)
        except Exception as ex:
            logging.error("Error in calculating RMSE.")
            logging.error(ex)
            raise ex
        return rmsescore

    def __rmse__(self,f):
        rmse = round(mean_squared_error(f['Prediction'], f["Actual"]) ** 0.5, 5)
        self.result = pd.DataFrame([[self.modelType,self.requiredColumns,self.futureCovariates,self.lookback,self.horizon,rmse]],columns=['Model',"Past Covariates","Future Covariates","Lookback","Horizon",'RMSE'])
        return rmse

    

    def predict(forecast_params,data=None):

        def getQuantileData(lst_pred,quantileListValues):
            lst_quantile = []
            for i in range(lst_pred.shape[1]):
                lst_quantile.append(np.quantile(lst_pred[:,i],quantileListValues))
            return lst_quantile
        
        def createdict(valu):
            dictvalue = {}
            for k,v in enumerate(valu.index) : 
                dictvalue[v] = valu[k]
            return dictvalue
        
        logging.info("Start: Model Prediction")  
        sourceModelPath = forecast_params["modelPath"]
        modelType = forecast_params["modelType"]
        horizon = forecast_params["horizon"]
        trunc = forecast_params["trunc"]
        targetColumn = forecast_params["targetColumn"]
        lookback = forecast_params["lookback"]
        dateField = forecast_params["dateField"]
        freq = forecast_params["freq"]
        frequency = forecast_params["frequency"]
        frequency_duration = forecast_params["frequency_duration"]
        multiplicationFactor = forecast_params["multiplicationFactor"]
        quantileList = forecast_params["quantileList"]
        quantileNames  = [str('p'+str(i)) for i in quantileList]
        quantileListValues = [i/100 for i in quantileList]
        originalDateFieldName = dateField+"Original"

        if len(forecast_params["predDate"]) == 0:
            dates = data.index.max()
        else:
            # Convert predDate to reindexed date
            forecast_params["predDate"] = data[data[originalDateFieldName]>=forecast_params["predDate"]].index.min()
            start = pd.to_datetime(forecast_params["predDate"])
            end = pd.to_datetime(data.index.max()) 
            dates = __generateDates__(start,end,str(horizon*frequency)+frequency_duration)
            data = data.drop([originalDateFieldName], axis=1)
        
        f = bz2.BZ2File(sourceModelPath+modelType+"/"+modelType+"_train.pkl",'rb')
        train_X, train_y, test_X, test_y, train_scaler,output_scaler, t_train_X, t_train_y, t_test_X, t_test_y,std_val = pickle.load(f)
        f.close()

        # with bz2.open(sourceModelPath+modelType+"/"+modelType+"_train.pkl",'rb') as f:
        #     train_X, train_y, test_X, test_y, train_scaler,output_scaler, t_train_X, t_train_y, t_test_X, t_test_y,std_val = f.read()
        # import gzip
        # with gzip.open(sourceModelPath+modelType+"/"+modelType+"_train.pkl"+'.gz', 'rb') as f_in, open(sourceModelPath+modelType+"/"+modelType+"_train.pkl", 'wb') as f_out:
        #     f_out.write(f_in.read())
        # with open(sourceModelPath+modelType+"/"+modelType+"_train.pkl", 'rb') as f:
        #     train_X, train_y, test_X, test_y, train_scaler,output_scaler, t_train_X, t_train_y, t_test_X, t_test_y,std_val = pickle.load(f)
        
        # Load all the models
        list_model = []
        for pred_idx in range(horizon):
            modelPath = sourceModelPath+modelType+'/model'+str(pred_idx)
            trainmodel = load_model(modelPath)
            list_model.append(trainmodel)
        
        post_model = []
        for i in range(horizon):
            modelPath = sourceModelPath +'/'+modelType+'/post_model_'+str(i)+'.h5'
            trainmodel = load_model(modelPath)
            post_model.append(trainmodel)
        predResult = []

        for date in dates:
            data_df = data[data.index<str(date)]
            pastDF = data_df[-trunc:] 
            predDF  = pastDF.copy()
            import random
            X_test_lst = []
            for _ in range(30):
                predDFTest = predDF.copy()
                for col in predDFTest.columns:
                    predDFTest[col] += np.random.normal(0,std_val[col],len(predDFTest))
                X_test_lst.append(predDFTest)
            X_test_lst.append(pastDF)
            
            samplesPred = []
            for past_dataset in X_test_lst :
                m = []
                t_test_X = []
                ik=0
                start = ik
                end = start
                # Scaling input dataset
                past_dataset = pd.DataFrame(train_scaler.transform(past_dataset), columns=past_dataset.columns,index=past_dataset.index)

                while(end<past_dataset.shape[0]): 
                    start = ik+1
                    end = start + trunc - horizon # 0 + 512 - 9 = 0, 503 | 1, 504 | 2, 505....... 9 , 512
                    ik=ik+1
                    data_df = past_dataset.iloc[start:end]
                    # print('*********')
                    # print("Value of Test start: " + str(data_df.index.values[start]))
                    # print("Value of Test end: " + str(data_df.index.values[data_df.shape[0]-1]))
                    # print("Test Data Length: "+ str(data_df.shape[0]))
                    _, _, _, _, test_uX, _ = golive_test_modules.convert_df_wavelet_input(data_df, targetColumn, True,lookback,horizon, 'bior3.5','periodic')
                    t_test_X.append(test_uX)
                    
                # prepare test_X

                test_X = t_test_X[0].copy()
                for ik in range(1,len(t_test_X)):
                    for jk in range(len(t_test_X[ik])):
                        test_X[jk] = np.append(test_X[jk], t_test_X[ik][jk], axis=0)
               
                # Run the prediction
                for i in range(0,horizon):
                    y_model = list_model[i].predict(test_X)[:,0,0]
                    df_yhat = pd.DataFrame(pd.DataFrame(y_model))
                    _,_,mix_test_X,_,_,_ = modelsvb.dl_preprocess_data(df_yhat, ts_lookback=horizon , ts_lookahead=horizon, pred_var_idx=0, validation=False, training=False)
                    my_model = post_model[i]
                    yhat_pp = my_model.predict(mix_test_X[:,:,0])
                    yhat_pp = yhat_pp[0]
                    m.extend(yhat_pp[-1:]) 
                yhat_mix = np.array(m)
                yhat_mix =np.array([yhat_mix])

                # Inverse transform - Scaling
                yhat_mix_list = []
                for jk in range(horizon):
                    yhat_mix_list.append(yhat_mix[0,jk])
                scaled_yhat_mix = output_scaler.inverse_transform(np.expand_dims(yhat_mix_list, axis=1))[:,0] #.clip(0,20)
                start = pd.to_datetime(past_dataset.index.max()) + timedelta(seconds = frequency*(3600/multiplicationFactor))
                end = pd.to_datetime(past_dataset.index.max()) + timedelta(seconds = frequency*(3600/multiplicationFactor)*horizon)
                dates = __generateDates__(start,end,freq)             
                output = scaled_yhat_mix
                samplesPred.append(output)
            predSeries = pd.DataFrame({'Pred':samplesPred[-1:][0], dateField: pd.DataFrame(dates)[0]})
            samplesPred = np.array(samplesPred)
            quantileData = getQuantileData(samplesPred,quantileListValues)
            quantileDf = pd.DataFrame(quantileData,columns = quantileNames)
            quantileDFDict = pd.DataFrame()
            quantileDictData = pd.DataFrame()
            for percentile in quantileNames :
                quantileDFDict[percentile] = quantileDf[percentile].values
            quantileDFDict['Quantile']  = quantileDFDict.apply(createdict,axis = 1)
            quantileDictData['Quantile'] = quantileDFDict['Quantile'] 
            predSeries = pd.concat([predSeries,quantileDictData],axis = 1)
            predResult.append(predSeries)   
        predSeries = pd.concat(predResult)
        print(predSeries)
        # Clean memory after prediction 
        del list_model
        del post_model
        del samplesPred
        gc.collect()
        return predSeries

    def prepareValResults(predSeries,data_df,errorAnalysisParams):
        try:
            print("Validation result preparation started")
            dateField = errorAnalysisParams.get("dateField")
            originalDateFieldName = dateField+"Original"
            
            multiplicationFactor = errorAnalysisParams.get("multiplicationFactor")
             
            # Map to reindexed dates
            if(errorAnalysisParams.get("isScore")):
                train_end = data_df[data_df[originalDateFieldName]<=errorAnalysisParams.get("train_end")].index.max()
                val_start = data_df[data_df[originalDateFieldName]>=errorAnalysisParams.get("val_start")].index.min()
                val_end = data_df[data_df[originalDateFieldName]<=errorAnalysisParams.get("val_end")].index.max()
            else:
                train_end = pd.to_datetime(errorAnalysisParams.get("train_end"))
                val_start = pd.to_datetime(errorAnalysisParams.get("val_start"))
                val_end = pd.to_datetime(errorAnalysisParams.get("val_end"))
            
            data_df.index = pd.to_datetime(data_df.index)
            
            actualSeries = data_df[data_df.index>=val_start]
            freq = int(errorAnalysisParams.get("frequency"))*int(errorAnalysisParams.get("horizon"))*int(3600/multiplicationFactor)

            lastTime = pd.to_datetime(val_end) + timedelta(seconds = errorAnalysisParams.get("frequency")*errorAnalysisParams.get("horizon")*(3600/multiplicationFactor))
            actualSeries = actualSeries[actualSeries.index<str(lastTime)]
            predSeries.reset_index()
            actualSeries[dateField] = pd.to_datetime(actualSeries.index)
            outputData = predSeries.merge(actualSeries,how = 'inner',on =dateField)   
            outputData = outputData.rename(columns={"Pred":"Prediction",errorAnalysisParams.get("targetColumn"):"Actual"})

            if(errorAnalysisParams.get("isScore") and errorAnalysisParams.get("descalingEnabled") and len(errorAnalysisParams.get("descalingColumn")) > 0):
                descalingColumn = errorAnalysisParams.get("descalingColumn")
                numberOfTurbines = errorAnalysisParams.get("numberOfTurbines")
                outputData['Actual'] = (outputData[descalingColumn]/numberOfTurbines)*outputData["Actual"]
                outputData['Prediction'] = (outputData[descalingColumn]/numberOfTurbines)*outputData["Prediction"]

            if not os.path.isdir("validate"):
                os.makedirs("validate")            
            # Save validation output
            outputData.to_csv("validate/"+errorAnalysisParams.get("modelType")+"_valResults.csv")
            return outputData
        except Exception as ex:
            logging.error("Error in model evaluation.")
            logging.error(ex)
            raise ex