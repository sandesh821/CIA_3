import pandas as pd
import numpy as np
import pylab as plt
import seaborn as sns
import os
import logging
import warnings
warnings.filterwarnings('ignore')
from sklearn.metrics import mean_squared_error ,mean_absolute_error
from  matplotlib.pyplot import axline
from sklearn.linear_model import LinearRegression
from azureml.core import Workspace
from azureml.core import Dataset, Datastore
from azureml.core import Run
from dboperations.dboperations import insertDataFromDF,executeStoredProcedure
from datetime import datetime

def getAMLWorkspace():
    try:
        ws = Workspace.from_config()
    except Exception as ex:
        logging.info("Reading workspace from run context")
        current_run = Run.get_context()
        ws = current_run.experiment.workspace
    return ws
decimal_points = 2

class ErrorAnalysis():

    def __init__(self,targetpath,sourcePath,pred_col,act_col,dat_col,units,modelName,start_date=None,end_date=None):
        self.pred_col = pred_col
        self.act_col = act_col
        self.targetpath = targetpath
        self.units = units
        self.decimal_points = decimal_points
        
        if not os.path.isdir(targetpath):
            os.makedirs(targetpath) 
        # Read data from datastore
        try:
            print("Reading from Blob storage")
            ws = getAMLWorkspace()
            datastore = ws.get_default_datastore()
            ds = Dataset.Tabular.from_delimited_files(path = [(datastore,sourcePath)],header='ALL_FILES_HAVE_SAME_HEADERS')
            df = ds.to_pandas_dataframe()
        except Exception as ex:
            print(ex)
            print("Reading from local path")
            df = pd.read_csv(sourcePath)
        
        self.tempdf = df.copy()
        self.tempdf.reset_index()
        self.tempdf['DateTime'] = pd.to_datetime(self.tempdf[dat_col])
        
        if len(df):
            df['DateTime'] = pd.to_datetime(df[dat_col])
            
            # Fill the gaps in the dates
            if(start_date is None and end_date is None):
                start_date = df['DateTime'].min()
                end_date = df['DateTime'].max()
            else:
                df = df[df['DateTime']>=start_date]
                df = df[df['DateTime']<=end_date]

            dates = pd.to_datetime(pd.date_range(start = str(start_date) , end = str(end_date) ,freq ="60min")) 
            
            df = df.set_index(pd.DatetimeIndex(df["DateTime"]))
            df = df.reindex(dates,fill_value=np.nan)

            df['hour'] = df['DateTime'].dt.hour
            df['abs_error']  =  np.absolute(df[self.pred_col]-df[self.act_col])
            df['error']  = df[self.act_col]-df[self.pred_col]

            # Calculate the values for temp dataframe
            self.tempdf['hour'] = self.tempdf['DateTime'].dt.hour
            self.tempdf['abs_error']  =  np.absolute(self.tempdf[self.pred_col]-self.tempdf[self.act_col])
            self.tempdf['error']  = self.tempdf[self.act_col]-self.tempdf[self.pred_col]
        else:
            print("No data for analysis")
        
        self.df = df
        
        # Dump Data to SQL-DB 
        ExperimentSet = targetpath.split("/")[1]
        Experiment = targetpath.split("/")[2] 
        InternalRunId = targetpath.split("/")[3]
        self.dumpdf = self.tempdf.copy()    # self.df.copy() was used earlier here
        self.dumpdf["ModelName"] = modelName
        self.dumpdf["ExperimentSet"] = ExperimentSet
        self.dumpdf["Experiment"] = Experiment
        self.dumpdf["InternalRunId"] = InternalRunId
        # single csv dump path
        self.df.to_csv(targetpath + "complete_error_analysis.csv",index=False)

        # Delete data if predictions for same run are present 
        try:
            executeStoredProcedure("usp_deleteErrorAnalysisData","@ModelName=?,@ExperimentSet=?,@Experiment=?,@InternalRunId=?",(modelName,ExperimentSet,Experiment,InternalRunId),"dbo",0)
        except Exception as ex:
            logging.info("Error in deleting records")
        
        # Rename DF for insertion
        insert_df = self.dumpdf[['ExperimentSet','Experiment','InternalRunId','DateTime','Actual','Prediction','Quantile','abs_error','error','ModelName']]

        insert_df = insert_df.rename(columns = {"abs_error":"AbsError","error":"Error"})
        # Insert Data into SQL-DB 
        if len(insert_df):
            try:
                insertDataFromDF(insert_df,"errorAnalysis")
                logging.info("Prediction data Succesfully Inserted")
            except Exception as e:
                print(e)
                # raise e

    def act_vs_pred_plot(self):      
        fig, ax = plt.subplots(figsize=(20,5))
        ax.plot(self.df['DateTime'], self.df[self.pred_col], linewidth = 1.0, alpha = 0.75,label='Prediction')
        ax.plot(self.df['DateTime'], self.df[self.act_col], linewidth = 1.0, alpha = 0.75,label='Actual')
        ax.legend()
        plt.title("Actual vs Predicted", fontsize=16)
        plt.xticks(rotation=10);
        # plt.ylabel('Wind speed '+self.units, fontsize=16)
        plt.tight_layout()
        print("Save charts to ", self.targetpath+'actvspre.png')
        plt.savefig(self.targetpath+'actvspre.png')
        plt.clf()
        plt.close()
    
    def nrmse_plot(self):

        rmse_df = self.tempdf.copy()
        rmse_df['DateTime'] = pd.to_datetime(rmse_df['DateTime'])
        rmse_df['hour'] = rmse_df['DateTime'].dt.hour
        rmse = []
        hour = []
        nrmse = []
        
        for i in rmse_df['hour'].unique():
            rm = rmse_df[rmse_df['hour'] == i]
            rmse_val = np.sqrt(np.mean(list((rm[self.pred_col] - rm[self.act_col])**2)))
            rmse.append(rmse_val)
            nrmse_val = round(rmse_val/ np.mean(rm[self.act_col]), self.decimal_points)
            nrmse.append(nrmse_val)
            print(nrmse_val)
            hour.append(i)
        final_rmse = pd.DataFrame({'rmse' : rmse , 'hour' : hour , 'nrmse' : nrmse  })
        final_rmse = final_rmse.sort_values(by='hour')
        print(final_rmse)
        plt.plot(final_rmse['hour'],final_rmse['nrmse'],'m--')
        plt.xlabel('Forecast Horizon')
        plt.ylabel('NRMSE')
        plt.title('NRMSE vs Forecast Horizon')
        plt.tight_layout()
        print("Save charts to ", self.targetpath+'ForecastHorizon_nRMSE_Analysis.png')
        plt.savefig(self.targetpath+'ForecastHorizon_nRMSE_Analysis.png')
        plt.clf()
        plt.close()
    
    def act_vs_pred_plot_withoutNaN(self):      
        fig, ax = plt.subplots(figsize=(20,5))
        ax.plot(self.tempdf.index, self.tempdf[self.pred_col], linewidth = 1.0, alpha = 0.75,label='Prediction')
        ax.plot(self.tempdf.index, self.tempdf[self.act_col], linewidth = 1.0, alpha = 0.75,label='Actual')
        ax.legend()
        plt.title("Actual vs Predicted without NaN values", fontsize=16)
        plt.xticks(rotation=10);
        plt.xlabel("DateTime",fontsize=16)
        plt.ylabel('Power '+self.units, fontsize=16)
        plt.tight_layout()
        plt.savefig(self.targetpath+'actvspre_withoutNaN.png')
        plt.clf()
        plt.close()

    def error_analysis(self):
        fig, ax = plt.subplots(figsize=(20,5))
        ax.plot(self.df['DateTime'], self.df['error'], linewidth = 1.0, alpha = 0.75)

        plt.xticks(rotation=10);
        plt.xlabel("DateTime",fontsize=16)
        plt.ylabel('Error', fontsize=16)
        plt.title("Max: "+ str(round(np.nanmax(self.df['error']),decimal_points)) + " Min: "+ str(round(np.nanmin(self.df['error']),decimal_points)) + " Mean: "+ str(round(np.nanmean(self.df['error']),decimal_points))+ " Standard Deviation: "+ str(round(np.nanstd(self.df['error']),decimal_points)) + " Median: "+ str(round(np.nanmedian(self.df['error']),decimal_points)), fontsize=16)
        plt.tight_layout()
        plt.savefig(self.targetpath+'error_analysis.png')
        plt.clf()
        plt.close()
    
    def error_analysis_withoutNaN(self):
        fig, ax = plt.subplots(figsize=(20,5))
        ax.plot(self.tempdf.index, self.tempdf['error'], linewidth = 1.0, alpha = 0.75)

        plt.xticks(rotation=10);
        # plt.xlabel("DateTime",fontsize=16)
        plt.ylabel('Error', fontsize=16)
        plt.title("Max: "+ str(round(np.nanmax(self.df['error']),decimal_points)) + " Min: "+ str(round(np.nanmin(self.df['error']),decimal_points)) + " Mean: "+ str(round(np.nanmean(self.df['error']),decimal_points))+ " Standard Deviation: "+ str(round(np.nanstd(self.df['error']),decimal_points)) + " Median: "+ str(round(np.nanmedian(self.df['error']),decimal_points)), fontsize=16)
        plt.tight_layout()
        plt.savefig(self.targetpath+'error_analysis_withoutNaN.png')
        plt.clf()
        plt.close()

    def absolute_error_analysis(self):
        fig, ax = plt.subplots(figsize=(20,5))
        ax.plot(self.df['DateTime'], self.df['abs_error'], linewidth = 1.0, alpha = 0.75)
        plt.xticks(rotation=10);
        plt.xlabel("DateTime",fontsize=16)
        plt.ylabel('Absolute Error', fontsize=16)
        plt.tight_layout()
        plt.savefig(self.targetpath+'absolute_error_analysis.png')
        plt.clf()
        plt.close()
    
    def absolute_error_analysis_withoutNaN(self):
        fig, ax = plt.subplots(figsize=(20,5))
        ax.plot(self.tempdf.index, self.tempdf['abs_error'], linewidth = 1.0, alpha = 0.75)
        plt.xticks(rotation=10);
        # plt.xlabel("DateTime",fontsize=16)
        plt.ylabel('Absolute Error', fontsize=16)
        plt.tight_layout()
        plt.savefig(self.targetpath+'absolute_error_analysis_withoutNaN.png')
        plt.clf()
        plt.close()

    def error_distribution_analysis(self):
        plt.figure(figsize=(20,5))
        plt.figure(figsize=(14,5))
        sns.boxplot(x="hour", y="error", data=self.df)
        plt.xticks(rotation=10);
        plt.xlabel("DateTime(Hour)",fontsize=16)
        plt.ylabel('Error Distribution', fontsize=16)
        plt.savefig(self.targetpath+'error_distribution_analysis.png')
        plt.clf()
        plt.close()
        sns.boxplot(x="hour", y="abs_error", data=self.df)
        plt.xticks(rotation=10);
        plt.xlabel("DateTime(Hour)",fontsize=16)
        plt.ylabel('Absolute Error Distribution', fontsize=16)
        plt.tight_layout()
        plt.savefig(self.targetpath+'absolute_error_distribution_analysis.png')
        plt.clf()
        plt.close()

    def r_squared(self):

        #initiate linear regression model
        data = self.df
        data.fillna(0,inplace = True)
        model = LinearRegression()
        #define predictor and response variables
        X, y = data[[self.act_col]], data[self.pred_col]
        #fit regression model
        model.fit(X, y)
        #calculate R-squared of regression model
        r_squared = model.score(X, y)
        #view R-squared value
        return r_squared

    def act_pred_scatter_plot(self):
        fig = plt.figure();
        plt.scatter(self.df[self.act_col], self.df[self.pred_col])
        axline((0, 0), (1, 1), linewidth=4, color='r')
        plt.xlabel(self.act_col)
        plt.ylabel(self.pred_col)
        #plt.title('{} vs {} Analysis'.format(self.act_col,pred_col))
        plt.tight_layout()
        r_squared = self.r_squared()
        fig.suptitle('R-Squared : {}'.format(r_squared), fontweight ="bold", fontsize=16) 
        #plt.savefig(self.targetpath+'{}_vs_{}_scatterplot.png'.format(self.act_col,self.pred_col))
        plt.clf()
        plt.close()
        temp = self.df[self.df[self.act_col] >0]
        sns.jointplot(x=temp[self.act_col], y=temp[self.pred_col], kind="hex", color="#4CB391")

        # sns.jointplot(x=self.df[self.act_col], y=self.df[self.pred_col], kind="hex", color="#4CB391")
        plt.title('{} vs {} Hexbin Analysis'.format(self.act_col,self.pred_col), fontsize=16)
        plt.tight_layout()
        plt.savefig(self.targetpath+'{}_vs_{}_hexbinplot.png'.format(self.act_col,self.pred_col))
        plt.clf()
        plt.close()


    def pdf_analysis(self):
        plt.hist(self.df['error'], histtype='step', bins=100)
        plt.title('PDF Analysis', fontsize=16)
        plt.tight_layout()
        plt.savefig(self.targetpath+'pdf_analysis.png')
        plt.clf()
        plt.close()

    def cdf_analysis(self):
        
        def ecdf(data):
            x = np.sort(data)
            n = x.size
            y = np.arange(1, n+1) / n
            return(x,y)
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()

        x_std1, y_std1 = ecdf(self.tempdf['error'])
        ax1.plot(x_std1, y_std1, marker='.', linestyle='none')
        ax1.set_xlabel('error')
        ax1.set_ylabel('cdf')

        ax2.hist(self.tempdf['error'], histtype='step', bins=100)
        ax2.set_ylabel('Frequency Distribution', fontsize=16)
        lb, ub = ax2.get_ylim()
        ax2.set_ylim(0,ub)
        plt.title('CDF Histogram Analysis', fontsize=16)
        plt.tight_layout()
        plt.savefig(self.targetpath+'cdf_histogram_analysis.png')
        plt.clf()
        plt.close()

    def mean_aboslute_err(self):
        return mean_absolute_error(self.tempdf[self.act_col], self.tempdf[self.pred_col]) 

    def mean_squared_err(self):
        return mean_squared_error(self.tempdf[self.act_col], self.tempdf[self.pred_col])
    
    def mean_absolute_percentage_error(self):
        y_true, y_pred = np.array(self.tempdf[self.act_col].values), np.array(self.tempdf[self.pred_col].values)
        return round(np.mean(np.abs((y_true - y_pred) / np.mean(y_true))) * 100, decimal_points)

    def normalized_root_mean_squared_error(self,rmse):
        y_pred = self.tempdf[self.pred_col]
        y_true = self.tempdf[self.act_col]
        return round(rmse/ np.mean(y_true), decimal_points)

    def evaluation_metrics(self,eval_met):
        fig, ax = plt.subplots()
        #hide the axes
        fig.patch.set_visible(False)
        ax.axis('off')
        ax.axis('tight')
        table = ax.table(cellText=eval_met.values, colLabels=eval_met.columns, loc='center')
        plt.tight_layout()
        plt.savefig(self.targetpath+'evaluation_metrics.png')
        plt.clf()
        plt.close()

def executeMain(sourcePath,targetPath,modelName,pred_col,act_col,dat_col,units,start_date=None,end_date=None):
    dataStorePath = sourcePath+'/'+modelName
    sourcePath = sourcePath+'/'+modelName+'_valResults.csv'
    resultDSPath = targetPath + modelName + "/erroranalysis/"
    error_plots = ErrorAnalysis(targetPath,sourcePath,pred_col,act_col,dat_col,units,modelName,start_date,end_date)
    if len(error_plots.df):
        error_plots.act_vs_pred_plot()
        error_plots.act_vs_pred_plot_withoutNaN()
        error_plots.error_analysis()
        error_plots.error_analysis_withoutNaN()
        error_plots.absolute_error_analysis()
        error_plots.absolute_error_analysis_withoutNaN()
        error_plots.error_distribution_analysis()
        error_plots.act_pred_scatter_plot()
        #error_plots.pdf_analysis()
        error_plots.cdf_analysis()
        mae = error_plots.mean_aboslute_err()
        mse = error_plots.mean_squared_err()
        mape = error_plots.mean_absolute_percentage_error()
        rmse = round(mse**0.5, decimal_points)
        nrmse = error_plots.normalized_root_mean_squared_error(rmse)
        eval_metrics = {'MAE' : round(mae, decimal_points) ,'MSE': mse,'MAPE': mape, 'RMSE' : rmse , 'nRMSE': nrmse}
        eval_metrics_df = pd.DataFrame([eval_metrics])
        eval_metrics_df["ModelName"] = modelName
        eval_metrics_df["ExperimentSet"] = targetPath.split("/")[1]
        eval_metrics_df["Experiment"] = targetPath.split("/")[2]     #.lower()  # change here 
        eval_metrics_df["InternalRunId"] = targetPath.split("/")[3]
        

        # Single row to insert to DB
        row = tuple(zip(eval_metrics_df["ModelName"],eval_metrics_df["ExperimentSet"],
        eval_metrics_df["Experiment"],eval_metrics_df["InternalRunId"],
        eval_metrics_df["MAE"],eval_metrics_df["MSE"],eval_metrics_df["MAPE"],
        eval_metrics_df["RMSE"],eval_metrics_df["nRMSE"]))[0]

        if len(eval_metrics_df):
            data = executeStoredProcedure("usp_InsertErrorAnalysisMetrics",
            "@ModelName=?,@ExperimentSet=?,@Experiment=?,@InternalRunID=?,@MAE=?,@MSE=?,@MAPE=?,@RMSE=?,@nRMSE=?",row,"dbo",0)
            print("Data Succesfully Inserted")


        eval_metrics_df.to_csv(targetPath+"eval_metrics.csv")
        error_plots.evaluation_metrics(eval_metrics_df)
        error_plots.nrmse_plot()

        ws = getAMLWorkspace()
        datastore = ws.get_default_datastore()
        datastore.upload(targetPath, target_path=resultDSPath, overwrite=True)

if __name__ == '__main__' :

    # Configuration for Error Analysis
    
    dataStorePath = "scores/experiment10002/20220829021520/DeepMC" 
    targetPath = "scores/experiment10002/20220829021520/"
    modelName = "DeepMC"
    pred_col = 'Prediction'
    act_col = 'Actual' 
    dat_col = 'DateTimeOriginal'
    start_date = None# '2022-02-07 02:00'
    end_date = None#'2022-02-26 05:00'
    units = '(MW)'

    executeMain(dataStorePath,targetPath,modelName,pred_col,act_col,dat_col,units,start_date,end_date)