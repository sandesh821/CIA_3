
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2022
-- Description: Insert experiment set transformation details
-- =============================================
CREATE PROCEDURE [golive].[usp_insertModelDetails] 
@ExperimentSetID int,
@ModelDetails NVARCHAR(MAX)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
  BEGIN
  DECLARE @IsDeleted INT = NULL
  IF EXISTS( SELECT 1 FROM golive.ModelSelection WHERE @ExperimentSetID = ExperimentSetID)
  BEGIN
		SET @IsDeleted = 1
	END
	INSERT INTO golive.ModelSelection
           (
			ExperimentSetID,
			ModelDetails,
			IsDeleted)
     VALUES
           (@ExperimentSetID
		   , @ModelDetails
		   , @IsDeleted
		 ) 
  END
END