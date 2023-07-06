
CREATE VIEW [dbo].[vw_SourceDataDetails]
AS
SELECT
    experimentSetid,
    MAX([Entity]) As EntityBlobName,MAX([PastCovariates]) As PastCovariatesBlobName,MAX([FutureCovariates]) As FutureCovariatesBlobName,
    MAX([Entity1]) As EntityTags,MAX([PastCovariates1]) As PastCovariatesTags,MAX([FutureCovariates1]) As FutureCovariatesTags,
    MAX([Entity2]) As EntityFileIdentifier,MAX([PastCovariates2]) As PastCovariatesFileIdentifier,MAX([FutureCovariates2]) As FutureCovariatesFileIdentifier,
	MAX([Entity3]) As EntityAccountName,MAX([PastCovariates3]) As PastCovariatesAccountName,MAX([FutureCovariates3]) As FutureCovariatesAccountName,
    MAX([Entity4]) As EntityContainerName,MAX([PastCovariates4]) As PastCovariatesContainerName,MAX([FutureCovariates4]) As FutureCovariatesContainerName
FROM
(
  SELECT 
   experimentSetid,
   FileType,
   FileType+'1' As FileType1,
   FileType+'2' As FileType2,
   FileType+'3' As FileType3,
   FileType+'4' As FileType4,
   STRING_AGG(BlobName,',') WITHIN GROUP (ORDER BY experimentSetid ASC, FileType) BlobName,
   STRING_AGG(Tags,',') WITHIN GROUP (ORDER BY experimentSetid ASC, FileType) Tags,
   STRING_AGG(FileIdentifier,',') WITHIN GROUP (ORDER BY experimentSetid ASC, FileType) FileIdentifier,
   STRING_AGG(AccountName,',') WITHIN GROUP (ORDER BY experimentSetid ASC, FileType) AccountName,
   STRING_AGG(ContainerName,',') WITHIN GROUP (ORDER BY experimentSetid ASC, FileType) ContainerName
  FROM dbo.experimentSetSourceDataDetails
  GROUP BY experimentSetid, FileType
 ) AS P

 -- For BlobName
 PIVOT
 (
   MAX(BlobName) FOR FileType IN ([Entity],[PastCovariates],[FutureCovariates])
 ) AS pv1

 -- For Tags
 PIVOT
 (
   MAX(Tags) FOR FileType1 IN ([Entity1],[PastCovariates1],[FutureCovariates1])
 ) AS pv2

 -- For FileIdentifier
 PIVOT
 (
   MAX(FileIdentifier) FOR FileType2 IN ([Entity2],[PastCovariates2],[FutureCovariates2])
 ) AS pv3

  -- For AccountName
 PIVOT
 (
   MAX(AccountName) FOR FileType3 IN ([Entity3],[PastCovariates3],[FutureCovariates3])
 ) AS pv4

  -- For FileIdentifier
 PIVOT
 (
   MAX(ContainerName) FOR FileType4 IN ([Entity4],[PastCovariates4],[FutureCovariates4])
 ) AS pv5
 Group BY experimentSetid