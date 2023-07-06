-- =============================================
-- Author:      Astha Agarwal
-- Create Date: December 12, 2022
-- Description: Insert experiment set details
-- =============================================
CREATE PROCEDURE [dbo].[usp_insertExperimentSetDetails] @ExperimentSetID int
, @SiteInformation NVARCHAR(MAX)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

  IF EXISTS (SELECT
      1
    FROM [dbo].[experimentSetSiteDetails]
    WHERE [ExperimentSetID] = @ExperimentSetID)
  BEGIN
    UPDATE [dbo].[experimentSetSiteDetails]
    SET SiteInformation = @SiteInformation
	WHERE [ExperimentSetID] = @ExperimentSetID
  END
  ELSE
  BEGIN
    INSERT INTO [dbo].[experimentSetSiteDetails] ([ExperimentSetID]
    , SiteInformation)
      VALUES (@ExperimentSetID,
              @SiteInformation)
  END
END