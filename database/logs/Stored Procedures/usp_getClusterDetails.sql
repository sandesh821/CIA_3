CREATE PROCEDURE [logs].[usp_getClusterDetails]
AS
BEGIN
	SET NOCOUNT ON;

	SELECT [Id]
		  ,[ClusterName]
		  ,[Cores]
		  ,[Ram]
	  FROM [logs].[clusterDetails]
END