
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2022
-- Description: Insert experiment set transformation details
-- =============================================
CREATE PROCEDURE [dbo].[usp_insertColumnTransformationDetails] 
@ExperimentSetID int,
@FileIdentifier VARCHAR(100),
@ColumnName VARCHAR(100),
@Transformations NVARCHAR(MAX)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
  BEGIN
    INSERT INTO [dbo].[columnTransformationDetails]
           (
			ExperimentSetID,
			FileIdentifier, 
			ColumnName,
			Transformations)
     VALUES
           (@ExperimentSetID
		   , @FileIdentifier
		   , @ColumnName
			,@Transformations )
  END
END