CREATE TABLE [dbo].[experimentSetSiteDetails] (
    [ExperimentSetID] INT            NULL,
    [SiteInformation] NVARCHAR (MAX) NULL,
    [CreatedBy]       VARCHAR (50)   DEFAULT (suser_sname()) NULL,
    [CreatedOn]       DATETIME       DEFAULT (getdate()) NULL
);

