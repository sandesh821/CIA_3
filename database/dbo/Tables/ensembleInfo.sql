CREATE TABLE [dbo].[ensembleInfo] (
    [ID]              INT            IDENTITY (1, 1) NOT NULL,
    [ExperimentSetID] INT            NULL,
    [EnsembleDetails] NVARCHAR (MAX) NOT NULL,
    [CreatedBy]       VARCHAR (100)  DEFAULT (suser_sname()) NULL,
    [CreatedOn]       DATETIME       DEFAULT (getdate()) NULL,
    [InternalRunId]   BIGINT         NULL
);

