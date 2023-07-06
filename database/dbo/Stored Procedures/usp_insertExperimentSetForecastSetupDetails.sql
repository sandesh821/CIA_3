
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: December 12, 2022
-- Description: Insert experiment set details
-- =============================================
CREATE PROCEDURE [dbo].[usp_insertExperimentSetForecastSetupDetails] @ExperimentSetID int,
@RowID int,
@Granularity int,
@GranularityUnits VARCHAR(10),
@InitialWindowSteps int,
@InitialWindowStepsUnits VARCHAR(10),
@ForecastHorizon int,
@ForecastHorizonUnits varchar(10),
@ForecastTime VARCHAR(100),
@Lookback int,
@TimeZone varchar(100)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

  IF EXISTS (SELECT
      1
    FROM [dbo].[experimentSetForecastSetupDetails]
    WHERE [ExperimentSetID] = @ExperimentSetID and [RowID] = @RowID)
  BEGIN
    UPDATE [dbo].[experimentSetForecastSetupDetails]
    SET [Granularity]					= @Granularity
           ,[GranularityUnits]			= @GranularityUnits
           ,[InitialWindowSteps]		= @InitialWindowSteps
           ,[InitialWindowStepsUnits]	= @InitialWindowStepsUnits
           ,[ForecastHorizon]			= @ForecastHorizon
           ,[ForecastHorizonUnits]		= @ForecastHorizonUnits
           ,[ForecastTime]				= @ForecastTime
		   ,[Lookback]					= @Lookback
           ,[TimeZone]					= @TimeZone
	WHERE [ExperimentSetID] = @ExperimentSetID and [RowID] = @RowID
  END
  ELSE
  BEGIN
    INSERT INTO [dbo].[experimentSetForecastSetupDetails]
           ([ExperimentSetID]
           ,[RowID]
           ,[Granularity]
           ,[GranularityUnits]
           ,[InitialWindowSteps]
           ,[InitialWindowStepsUnits]
           ,[ForecastHorizon]
           ,[ForecastHorizonUnits]
           ,[ForecastTime]
		   ,[Lookback]
           ,[TimeZone])
     VALUES
           (@ExperimentSetID
           ,@RowID
           ,@Granularity
           ,@GranularityUnits
           ,@InitialWindowSteps
           ,@InitialWindowStepsUnits
           ,@ForecastHorizon
           ,@ForecastHorizonUnits
           ,@ForecastTime
		   ,@Lookback
           ,@TimeZone)
  END
END