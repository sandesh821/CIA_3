-- =============================================
-- Author:      Astha Agarwal
-- Create Date: December 28, 2022
-- Description: Get wind turbines information
-- =============================================
CREATE PROCEDURE [dbo].[usp_getWindTurbines]
AS
BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
    SET NOCOUNT ON

    -- Insert statements for procedure here
    SELECT * from static.windturbines (NOLOCK)

END