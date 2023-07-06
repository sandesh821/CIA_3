
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: December 12, 2022
-- Description: Get experiment set forecast setup details
-- =============================================
CREATE PROCEDURE [dbo].[usp_getExperimentSetForecastSetupDetails] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

  SELECT
           [Granularity]
           ,[GranularityUnits]
           ,[InitialWindowSteps]
           ,[InitialWindowStepsUnits]
           ,[ForecastHorizon]
           ,[ForecastHorizonUnits]
           ,[ForecastTime]
		   ,[Lookback]
           ,[TimeZone]
		   FROM [dbo].[experimentSetForecastSetupDetails]
		   WHERE [ExperimentSetID] = @ExperimentSetID
		   order by [RowID]
END