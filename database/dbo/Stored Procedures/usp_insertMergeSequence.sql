
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2022
-- Description: Insert experiment set transformation details
-- =============================================
CREATE PROCEDURE [dbo].[usp_insertMergeSequence] 
@ExperimentSetID int,
@initFile [varchar](1000),
@operators [nvarchar](max),
@fileIdentifiers [nvarchar](max)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
  BEGIN
    INSERT INTO [dbo].[mergeFileSequence]
           (
			ExperimentSetID,
			[initFile] ,
			[operators],
			[fileIdentifiers])
     VALUES
           (@ExperimentSetID
		   , @initFile
		   , @operators
		   , @fileIdentifiers)
  END
END