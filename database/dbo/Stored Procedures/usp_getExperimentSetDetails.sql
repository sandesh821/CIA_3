-- =============================================
-- Author:      Astha Agarwal
-- Create Date: December 28, 2022
-- Description: Get experiment set site information
-- =============================================
CREATE PROCEDURE [dbo].[usp_getExperimentSetDetails]
@ExperimentSetID int
AS
BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
    SET NOCOUNT ON

    -- Insert statements for procedure here
    SELECT SiteInformation FROM [dbo].[experimentSetSiteDetails] (NOLOCK)
    WHERE [ExperimentSetID] = @ExperimentSetID 

END