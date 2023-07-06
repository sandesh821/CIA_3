CREATE TABLE [golive].[dataDrift] (
    [Id]              INT            IDENTITY (1, 1) NOT NULL,
    [ExperimentSetId] INT            NULL,
    [DriftResponse]   VARCHAR (8000) NULL,
    [Type]            VARCHAR (100)  NULL,
    [CreatedDate]     DATE           DEFAULT (getdate()) NULL,
    [CreatedBy]       VARCHAR (100)  DEFAULT (suser_sname()) NOT NULL
);

