CREATE TABLE [dbo].[transformationDetails] (
    [ID]              INT            IDENTITY (1, 1) NOT NULL,
    [ExperimentSetID] INT            NULL,
    [FileIdentifier]  VARCHAR (100)  NOT NULL,
    [Transformations] NVARCHAR (MAX) NOT NULL,
    [CreatedBy]       VARCHAR (100)  DEFAULT (suser_sname()) NULL,
    [CreatedOn]       DATETIME       DEFAULT (getdate()) NULL
);

