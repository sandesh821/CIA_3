CREATE TABLE [dbo].[experimentsList] (
    [ID]               INT            IDENTITY (1, 1) NOT NULL,
    [ExperimentSetID]  INT            NULL,
    [ExperimentTag]    VARCHAR (100)  NOT NULL,
    [Algorithm]        VARCHAR (100)  NOT NULL,
    [PastCovariates]   VARCHAR (1000) NOT NULL,
    [FutureCovariates] VARCHAR (1000) NOT NULL,
    [Entity]           VARCHAR (100)  NOT NULL,
    [TrainStart]       VARCHAR (100)  NOT NULL,
    [TrainEnd]         VARCHAR (100)  NOT NULL,
    [ValStart]         VARCHAR (100)  NOT NULL,
    [ValEnd]           VARCHAR (100)  NOT NULL,
    [TestStart]        VARCHAR (100)  NOT NULL,
    [TestEnd]          VARCHAR (100)  NOT NULL,
    [CreatedBy]        VARCHAR (100)  DEFAULT (suser_sname()) NULL,
    [CreatedOn]        DATETIME       DEFAULT (getdate()) NULL,
    [Status]           VARCHAR (10)   NULL,
    [quantileList]     VARCHAR (100)  NULL
);



