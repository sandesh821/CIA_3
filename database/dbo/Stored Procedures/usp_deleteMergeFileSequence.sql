


-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2023
-- Description: Delete experiment set merge file sequence
-- =============================================
CREATE PROCEDURE [dbo].[usp_deleteMergeFileSequence] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

  DELETE FROM [dbo].[mergeFileSequence]
		   WHERE [ExperimentSetID] = @ExperimentSetID
END