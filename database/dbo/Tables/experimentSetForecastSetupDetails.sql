CREATE TABLE [dbo].[experimentSetForecastSetupDetails] (
    [ID]                      INT           IDENTITY (1, 1) NOT NULL,
    [ExperimentSetID]         INT           NULL,
    [RowID]                   INT           NULL,
    [Granularity]             INT           NULL,
    [GranularityUnits]        VARCHAR (10)  NULL,
    [InitialWindowSteps]      INT           NULL,
    [InitialWindowStepsUnits] VARCHAR (10)  NULL,
    [ForecastHorizon]         INT           NULL,
    [ForecastHorizonUnits]    VARCHAR (10)  NULL,
    [ForecastTime]            VARCHAR (100) NULL,
    [Lookback]                INT           NULL,
    [TimeZone]                VARCHAR (100) NULL,
    [CreatedBy]               VARCHAR (50)  DEFAULT (suser_sname()) NULL,
    [CreatedOn]               DATETIME      DEFAULT (getdate()) NULL,
    PRIMARY KEY CLUSTERED ([ID] ASC)
);



