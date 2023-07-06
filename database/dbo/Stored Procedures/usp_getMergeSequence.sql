
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: April 19, 2023
-- Description: Get experiment set merge sequence details
-- EXEC [dbo].[usp_getMergeSequence] 38
-- =============================================
CREATE PROCEDURE [dbo].[usp_getMergeSequence] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		SELECT
			[initFile] ,
			[operators],
			[fileIdentifiers]
		FROM [dbo].[mergeFileSequence]
		WHERE [ExperimentSetID] = @ExperimentSetID
END