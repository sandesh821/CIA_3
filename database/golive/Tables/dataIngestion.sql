CREATE TABLE [golive].[dataIngestion] (
    [ID]                 INT             IDENTITY (1, 1) NOT NULL,
    [ExperimentSetID]    INT             NULL,
    [SourceDataDetails]  NVARCHAR (MAX)  NULL,
    [DataRefreshDetails] NVARCHAR (MAX)  NOT NULL,
    [CreatedBy]          VARCHAR (100)   DEFAULT (suser_sname()) NULL,
    [CreatedOn]          DATETIME        DEFAULT (getdate()) NULL,
    [ApiMapping]         NVARCHAR (2000) NULL
);

