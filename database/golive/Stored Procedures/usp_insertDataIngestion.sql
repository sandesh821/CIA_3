
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 30, 2023
-- Description: Insert go live data ingestion details
-- =============================================
CREATE PROCEDURE [golive].[usp_insertDataIngestion] 
@ExperimentSetID int,
@SourceDataDetails NVARCHAR(MAX),
@DataRefreshDetails NVARCHAR(MAX),
@ApiMapping NVARCHAR(2000)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
  BEGIN
    INSERT INTO golive.dataIngestion
           (
			ExperimentSetID,
			[SourceDataDetails], 
			[DataRefreshDetails],
			[ApiMapping])
     VALUES
           (@ExperimentSetID
		   , @SourceDataDetails
		   , @DataRefreshDetails
		   , @ApiMapping
		 )
  END
END