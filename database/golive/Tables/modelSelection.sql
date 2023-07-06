CREATE TABLE [golive].[modelSelection] (
    [ID]              INT            IDENTITY (1, 1) NOT NULL,
    [ExperimentSetID] INT            NULL,
    [ModelDetails]    NVARCHAR (MAX) NOT NULL,
    [IsDeleted]       SMALLINT       NULL,
    [CreatedBy]       VARCHAR (100)  DEFAULT (suser_sname()) NULL,
    [CreatedOn]       DATETIME       DEFAULT (getdate()) NULL
);



