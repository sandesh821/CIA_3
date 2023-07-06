CREATE PROCEDURE [dbo].[usp_InsertErrorAnalysisMetrics] 
       @ModelName VARCHAR(100), 
       @ExperimentSet VARCHAR(100), 
       @Experiment VARCHAR(100),
			 @InternalRunId BIGINT,
			 @MAE FLOAT,
			 @MSE FLOAT,
			 @MAPE FLOAT,
			 @RMSE FLOAT,
			 @nRMSE FLOAT								  
AS 
BEGIN 
     SET NOCOUNT ON 

	 IF EXISTS (
		SELECT 1 FROM [dbo].[errorAnalysisMetrics]
		WHERE ExperimentSet = @ExperimentSet
			AND Experiment = @Experiment
			AND InternalRunId = @InternalRunId
			AND ModelName = @ModelName
	 )
	 BEGIN
		UPDATE [dbo].[errorAnalysisMetrics]
		SET MAE = @MAE,
		MSE = @MSE,
		MAPE = @MAPE,
		RMSE = @RMSE,
		nRMSE = @nRMSE
		WHERE ExperimentSet = @ExperimentSet
			AND Experiment = @Experiment
			AND InternalRunId = @InternalRunId
			AND ModelName = @ModelName
	 END

	 ELSE
	 BEGIN
     INSERT INTO [dbo].[errorAnalysisMetrics]
          (                    
           ModelName,ExperimentSet,Experiment,InternalRunId,MAE,MSE,MAPE,RMSE,nRMSE
          ) 
     VALUES 
          ( 
           @ModelName,@ExperimentSet,@Experiment,@InternalRunId,@MAE,@MSE,@MAPE,@RMSE,@nRMSE
          ) 
	END
END