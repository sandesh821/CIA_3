-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 28, 2022
-- Description: Get geographies list
-- =============================================
CREATE PROCEDURE [dbo].[usp_saveSelectedGeography]
@ExperimentSetID INT,
@GeographyName varchar(50)
AS
BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
    SET NOCOUNT ON

	IF EXISTS ( SELECT 1 FROM dbo.experimentSetAzureGeography WHERE ExperimentSetID = @ExperimentSetID)
	BEGIN
		UPDATE dbo.experimentSetAzureGeography
		SET GeographyName = @GeographyName
		WHERE ExperimentSetID = @ExperimentSetID
	END
	ELSE
    BEGIN
		-- Insert statements for procedure here
		INSERT INTO dbo.experimentSetAzureGeography(
			ExperimentSetID, GeographyName
		)
		VALUES (@ExperimentSetID,@GeographyName)
	END
END