CREATE TABLE [dbo].[experimentSetSourceDataDetails] (
    [ID]              INT           IDENTITY (1, 1) NOT NULL,
    [ExperimentSetID] INT           NULL,
    [RowID]           INT           NULL,
    [FileType]        VARCHAR (100) NULL,
    [AccountName]     VARCHAR (100) NULL,
    [ContainerName]   VARCHAR (100) NULL,
    [BlobName]        VARCHAR (100) NULL,
    [Tags]            VARCHAR (100) NULL,
    [FileIdentifier]  VARCHAR (100) NULL,
    [CreatedBy]       VARCHAR (50)  DEFAULT (suser_sname()) NULL,
    [CreatedOn]       DATETIME      DEFAULT (getdate()) NULL,
    PRIMARY KEY CLUSTERED ([ID] ASC)
);

