
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 28, 2022
-- Description: Get geographies list
-- =============================================
CREATE PROCEDURE [dbo].[usp_getGeographies]
AS
BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
    SET NOCOUNT ON

    -- Insert statements for procedure here
    SELECT * from static.AzureGeography (NOLOCK)

END