
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2022
-- Description: Insert experiment set source data timezone details
-- =============================================
CREATE PROCEDURE [dbo].[usp_insertTransformationFileTimezoneDetails] 
@ExperimentSetID int,
@TimeZoneDetails NVARCHAR(MAX)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
  BEGIN
    INSERT INTO [dbo].[transformationFileTimezoneDetails]
           (
		   ExperimentSetID,
		   TimeZoneDetails)
     VALUES
           (@ExperimentSetID
           ,@TimeZoneDetails)
  END
END