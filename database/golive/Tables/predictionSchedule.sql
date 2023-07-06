CREATE TABLE [golive].[predictionSchedule] (
    [ID]                     INT           IDENTITY (1, 1) NOT NULL,
    [ExperimentSetId]        INT           NOT NULL,
    [PredictionDate]         VARCHAR (100) NULL,
    [Status]                 VARCHAR (20)  NULL,
    [CreatedOn]              DATETIME      DEFAULT (getdate()) NULL,
    [CreatedBy]              VARCHAR (100) DEFAULT (suser_sname()) NULL,
    [MergedResampling]       SMALLINT      NULL,
    [APIDataRefresh]         SMALLINT      NULL,
    [DataCleaning]           SMALLINT      NULL,
    [DataDriftValidation]    SMALLINT      NULL,
    [ModelDriftValidation]   SMALLINT      NULL,
    [PreviousPredictionDate] DATETIME      NULL
);

