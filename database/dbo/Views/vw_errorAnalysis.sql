CREATE view [dbo].[vw_errorAnalysis] AS

SELECT CreatedOn, ModelName, ExperimentSet, Experiment, Quantile,BiasCorrection,key_value,percentile_key,percentile_value,
InternalRunId, Actual, Prediction, AbsError, Error, DateTime, 
ABS(Prediction - Actual) AS Act_pred, POWER(ABS(Prediction - Actual), 2) AS Act_pred_2, 
DATEPART(HOUR, DateTime) AS Hour, DATEPART(MINUTE, DateTime) 
             AS Minute, DATEPART(SECOND, DateTime) AS Second, DATENAME(M, DateTime) AS MonthName 
FROM  [dbo].[errorAnalysis_Quantile_Unpivot]