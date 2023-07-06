-- =============================================
-- Author:      Astha Agarwal
-- Create Date: December 12, 2022
-- Description: Insert experiment set details
-- =============================================
CREATE PROCEDURE [dbo].[usp_insertExperimentSetSourceDataDetails] @ExperimentSetID int,
@RowID int,
@FileType [varchar](100) NULL,
@AccountName [varchar](100) NULL,
@ContainerName [varchar](100) NULL,
@BlobName [varchar](100) NULL,
@Tag [varchar](100) NULL,
@FileIdentifier [varchar](100) NULL
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

  IF EXISTS (SELECT
      1
    FROM [dbo].[experimentSetSourceDataDetails]
    WHERE [ExperimentSetID] = @ExperimentSetID and [RowID] = @RowID)
  BEGIN
    UPDATE [dbo].[experimentSetSourceDataDetails]
    SET FileType			= @FileType ,
		AccountName 		= @AccountName ,
		ContainerName 		= @ContainerName ,
		BlobName 			= @BlobName ,
		Tags 				= @Tag ,
		FileIdentifier 		= @FileIdentifier
	WHERE [ExperimentSetID] = @ExperimentSetID and [RowID] = @RowID
  END
  ELSE
  BEGIN
    INSERT INTO [dbo].[experimentSetSourceDataDetails]
           ([ExperimentSetID],
            [RowID],
			[FileType] ,
			[AccountName] ,
			[ContainerName] ,
			[BlobName] ,
			[Tags] ,
			[FileIdentifier])
     VALUES
           (@ExperimentSetID
           ,@RowID
		   ,@FileType		
		   ,@AccountName 	
		   ,@ContainerName 	
		   ,@BlobName 		
		   ,@Tag		
		   ,@FileIdentifier)
  END
END