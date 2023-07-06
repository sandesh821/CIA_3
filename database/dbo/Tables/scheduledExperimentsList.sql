CREATE TABLE [dbo].[scheduledExperimentsList] (
    [ID]                INT            IDENTITY (1, 1) NOT NULL,
    [ExperimentSetID]   VARCHAR (100)  NOT NULL,
    [ExperimentSetName] VARCHAR (100)  NOT NULL,
    [experimenttag]     VARCHAR (100)  NOT NULL,
    [algorithm]         VARCHAR (100)  NOT NULL,
    [PastCovariates]    VARCHAR (1000) NOT NULL,
    [FutureCovariates]  VARCHAR (1000) NOT NULL,
    [Entity]            VARCHAR (100)  NOT NULL,
    [ReindexCols]       VARCHAR (8000) NULL,
    [TrainStart]        VARCHAR (100)  NOT NULL,
    [TrainEnd]          VARCHAR (100)  NOT NULL,
    [ValStart]          VARCHAR (100)  NOT NULL,
    [ValEnd]            VARCHAR (100)  NOT NULL,
    [TestStart]         VARCHAR (100)  NOT NULL,
    [TestEnd]           VARCHAR (100)  NOT NULL,
    [ForecastHorizon]   VARCHAR (100)  NULL,
    [Granularity]       VARCHAR (100)  NULL,
    [GranularityUnits]  VARCHAR (100)  NULL,
    [MergedFile]        VARCHAR (50)   NULL,
    [ForecastTime]      VARCHAR (100)  NULL,
    [Status]            INT            DEFAULT ((0)) NOT NULL,
    [CreatedBy]         VARCHAR (100)  DEFAULT (suser_sname()) NOT NULL,
    [CreatedOn]         DATETIME       DEFAULT (getdate()) NOT NULL,
    [Lookback]          INT            NULL,
    [quantileList]      VARCHAR (100)  NULL,
    [CreatedSource]     VARCHAR (50)   DEFAULT ('workflow') NULL
);







