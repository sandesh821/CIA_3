-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2023
-- Description: Get experiment set transformation details
-- exec [dbo].[usp_getAllScheduledExperimentsList] 33
-- =============================================
CREATE PROCEDURE [dbo].[usp_getAllScheduledExperimentsList] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		SELECT distinct
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
			EL.Lookback AS LookBack,
			'PreprocessedFile.csv' AS MergedFile,
			ForecastTime,
			SD.*,
			RT.AMLRunId,
			ISNULL(RT.InternalRunID,'') InternalRunID,
			CASE 
				WHEN EL.Status = 0 THEN 'To be executed'
				WHEN EL.Status = 1 OR EL.Status = 2 OR EL.Status = 3 THEN RT.RunStatus
				WHEN EL.Status = 4 THEN 'Batch Scoring Started'
				WHEN EL.Status = 5 THEN 'Batch Scoring Finished'
			END AS RunStatus,
			EL.Status,
			CONVERT(INT,REPLACE(experimenttag,'experiment','')) expnum
		FROM [dbo].[scheduledExperimentsList] EL
		INNER JOIN dbo.vw_SourceDataDetails SD
		ON SD.ExperimentSetID = EL.ExperimentSetID
		LEFT JOIN ( SELECT * FROM [logs].[runTracker] WHERE RunStatus NOT LIKE 'Batch%') RT
		ON RT.ExperimentSet = EL.[ExperimentSetName]
		AND EL.experimenttag = RT.Experiment
		WHERE EL.[ExperimentSetID] = @ExperimentSetID
		ORDER BY expnum
END