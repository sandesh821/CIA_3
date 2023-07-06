-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2023
-- Modified By: Kritarth Sain
-- Modified Date: April 4, 2023
-- Description: Get experiment set transformation details
-- EXeC [dbo].[usp_getExperimentsList] 1
-- =============================================
CREATE PROCEDURE [dbo].[usp_getExperimentsList] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		SELECT
			ExperimentTag ,
			CONVERT(INT,REPLACE(ExperimentTag,'experiment','')) AS ExperimentNumber ,
			[Algorithm] ,
			PastCovariates,
			FutureCovariates,
			REPLACE(ISNULL(PastCovariates, '') + ISNULL( FutureCovariates,''),'''][''',''',''') AS FeatureList,
			Entity,
			TrainStart ,
			TrainEnd ,
			ValStart ,
			ValEnd ,
			TestStart ,
			TestEnd ,
			[Status],
			quantileList
		FROM [dbo].[experimentsList]
		WHERE [ExperimentSetID] = @ExperimentSetID
END