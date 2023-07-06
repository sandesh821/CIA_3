CREATE TABLE [dbo].[experimentSetAzureGeography] (
    [ID]              INT          IDENTITY (1, 1) NOT NULL,
    [ExperimentSetID] INT          NOT NULL,
    [GeographyName]   VARCHAR (15) NULL,
    [CreatedBy]       VARCHAR (50) DEFAULT (suser_sname()) NULL,
    [CreatedOn]       DATETIME     DEFAULT (getdate()) NULL,
    PRIMARY KEY CLUSTERED ([ExperimentSetID] ASC)
);

