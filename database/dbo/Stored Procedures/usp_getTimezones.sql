
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 03, 2022
-- Description: Get timezones information
-- =============================================
CREATE PROCEDURE [dbo].[usp_getTimezones]
AS
BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
    SET NOCOUNT ON

    -- Insert statements for procedure here
    SELECT * from static.timezones (NOLOCK)

END