-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2023
-- Description: Get experiment list for pipeline
--EXEC [dbo].[usp_getExperimentsListForPipeline] 
-- =============================================
CREATE PROCEDURE [dbo].[usp_getExperimentsListForPipeline]
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
		SELECT
			ROW_NUMBER() OVER(ORDER BY ExperimentTag) AS [sno],
			[ExperimentSetName],
			experimenttag,
			[algorithm],
			PastCovariates,
			FutureCovariates,
			Entity ,
			ReindexCols AS ReindexCols,
			TrainStart ,
			TrainEnd ,
			ValStart ,
			ValEnd ,
			TestStart ,
			TestEnd  ,
			ForecastHorizon,
			Granularity,
			GranularityUnits,
			EL.MergedFile,
			ForecastTime,
			ISNULL(Lookback, 24) Lookback,
			ISNULL(G.GeographyName, 'US') GeographyName,
			ISNULL(RS.InternalRunID,' ') InternalRunID,
			[Status],
			[quantileList]
		FROM [dbo].[scheduledExperimentsList] EL
		LEFT JOIN [dbo].[experimentSetAzureGeography] G
		ON G.ExperimentSetID = EL.ExperimentSetID
		LEFT JOIN (
			SELECT experimentSet, experiment, MAX(InternalRunID) InternalRunID FROM logs.runTracker
			WHERE RunStatus = 'Finished'
			GROUP BY experimentSet, experiment
		) RS
		ON EL.ExperimentSetName = RS.ExperimentSet
		AND EL.experimenttag = RS.Experiment
		WHERE ([Status] = 0 OR [Status] = 3)

END