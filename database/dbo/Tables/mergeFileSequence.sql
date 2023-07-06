CREATE TABLE [dbo].[mergeFileSequence] (
    [ID]              INT            IDENTITY (1, 1) NOT NULL,
    [ExperimentSetID] INT            NULL,
    [initFile]        VARCHAR (1000) NOT NULL,
    [operators]       NVARCHAR (MAX) NOT NULL,
    [fileIdentifiers] NVARCHAR (MAX) NOT NULL,
    [CreatedBy]       VARCHAR (100)  DEFAULT (suser_sname()) NULL,
    [CreatedOn]       DATETIME       DEFAULT (getdate()) NULL
);

