
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2022
-- Description: Insert experiment set transformation details
-- =============================================
CREATE PROCEDURE [dbo].[usp_insertTransformationDetails] 
@ExperimentSetID int,
@FileIdentifier VARCHAR(100),
@Transformations NVARCHAR(MAX)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
  BEGIN
    INSERT INTO [dbo].transformationDetails
           (
			ExperimentSetID,
			FileIdentifier, 
			Transformations)
     VALUES
           (@ExperimentSetID
		   , @FileIdentifier
			,@Transformations )
  END
END