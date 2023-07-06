-- =============================================
-- Author:      Astha Agarwal
-- Modified By: Haridas Sai Prakash
-- Create Date: January 13, 2023
-- Modified Date: March 31, 2023
-- Description: Get experiment list for suggestions
-- EXeC [dbo].[usp_getExperimentsListforsuggestions] 1
-- =============================================
CREATE PROCEDURE [dbo].[usp_getExperimentsListforsuggestions] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
        
		SELECT ea.RMSE, el.ExperimentTag ,
		CONVERT(INT,REPLACE(el.ExperimentTag,'experiment','')) AS ExperimentNumber ,
		el.Algorithm ,
		el.PastCovariates,
		el.FutureCovariates,
		REPLACE(ISNULL(el.PastCovariates, '') + ISNULL( el.FutureCovariates,''),'''][''',''',''') AS FeatureList,
		el.Entity
		FROM errorAnalysisMetrics ea
		INNER JOIN scheduledExperimentsList se
		ON se.ExperimentSetName = ea.ExperimentSet
		INNER JOIN experimentsList el
		ON el.ExperimentSetID = se.ExperimentSetID
		WHERE se.Status = '5' AND el.ExperimentSetID = @ExperimentSetID
		
		
END