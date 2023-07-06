-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2023
-- Modified Date : April 3 2023 [Desc : Added Quantile List]
-- Description: Schedule experiments
--EXEC [dbo].[usp_scheduleExperimentsListForPipeline] 33
-- =============================================
CREATE  PROCEDURE [dbo].[usp_scheduleExperimentsListForPipeline] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
		

		INSERT INTO [dbo].[scheduledExperimentsList]
           ([ExperimentSetID]
           ,[ExperimentSetName]
           ,[experimenttag]
           ,[algorithm]
           ,[PastCovariates]
           ,[FutureCovariates]
           ,[Entity]
           ,[ReindexCols]
           ,[TrainStart]
           ,[TrainEnd]
           ,[ValStart]
           ,[ValEnd]
           ,[TestStart]
           ,[TestEnd]
           ,[ForecastHorizon]
           ,[Granularity]
           ,[GranularityUnits]
           ,[MergedFile]
           ,[ForecastTime]
		   ,[Lookback]
		   ,[quantileList])
		SELECT
			EL.[ExperimentSetID],
			ES.[ExperimentSetName],
			ExperimentTag AS experimenttag,
			[Algorithm] AS [algorithm],
			PastCovariates,
			FutureCovariates,
			Entity ,
			CASE WHEN FutureCovariates = '[]' THEN REPLACE(PastCovariates,']',',''') + Entity + ''']'
					WHEN PastCovariates = '[]' THEN REPLACE(FutureCovariates,']',',''') + Entity + ''']'
				ELSE REPLACE(REPLACE(PastCovariates+FutureCovariates,'][',','),']',',''') + Entity + ''']' END AS ReindexCols,
			TrainStart ,
			TrainEnd ,
			ValStart ,
			ValEnd ,
			TestStart ,
			TestEnd  ,
			FSD.ForecastHorizon,
			FSD.Granularity,
			FSD.GranularityUnits,
			'MergedFiles/PreprocessedFile.csv' AS MergedFile,
			FSD.ForecastTime,
			FSD.Lookback ,
			EL.[quantileList]
		FROM [dbo].[experimentsList] EL
		INNER JOIN (select TOP 1
				ExperimentSetID,
				--STRING_AGG(ForecastTime, ',') ForecastTime
				--,  STRING_AGG(Granularity, ',') Granularity
				--,  STRING_AGG(GranularityUnits, ',')  GranularityUnits
				--,  STRING_AGG(ForecastHorizon, ',') ForecastHorizon
				ForecastTime,
				Granularity,
				GranularityUnits,
				ForecastHorizon,
				Lookback
			from dbo.experimentSetForecastSetupDetails 
			WHERE ExperimentSetID = @ExperimentSetID
			--GROUP BY ExperimentSetID
			) FSD
		ON EL.[ExperimentSetID] = FSD.[ExperimentSetID]
		INNER JOIN [dbo].[experimentSet] ES
		ON EL.[ExperimentSetID] = ES.[ExperimentSetID]
		WHERE EL.[ExperimentSetID] = @ExperimentSetID
		AND EL.[Status] IS NULL

		-- Update the experiments status to 'Scheduled'
		UPDATE [dbo].[experimentsList]
		SET [Status] = 'Scheduled'
		WHERE [ExperimentSetID] =  @ExperimentSetID
		AND [Status] IS NULL
END