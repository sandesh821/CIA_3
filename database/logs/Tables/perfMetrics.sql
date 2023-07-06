CREATE TABLE [logs].[perfMetrics] (
    [Id]                   INT          IDENTITY (1, 1) NOT NULL,
    [ProcessName]          VARCHAR (50) NOT NULL,
    [PID]                  BIGINT       NOT NULL,
    [PPID]                 BIGINT       NOT NULL,
    [MF_ResidentSetSize]   BIGINT       NOT NULL,
    [MF_VirtualMemorySize] BIGINT       NOT NULL,
    [MF_Shared]            BIGINT       NOT NULL,
    [MF_TextResidentSet]   BIGINT       NOT NULL,
    [MF_DataResidentSet]   BIGINT       NOT NULL,
    [MF_Dirty]             BIGINT       NOT NULL,
    [CpuPercentage]        FLOAT (53)   NOT NULL,
    [CpuNum]               BIGINT       NOT NULL,
    [CpuTimes]             FLOAT (53)   NOT NULL,
    [CreatedBy]            VARCHAR (50) CONSTRAINT [DF_perfMetrics_CreatedBy] DEFAULT ('admin') NULL,
    [CreatedOn]            DATETIME     CONSTRAINT [DF_perfMetrics_CreatedOn] DEFAULT (getdate()) NULL,
    CONSTRAINT [PK_PerfMetrics_IdProcessName] PRIMARY KEY CLUSTERED ([Id] ASC, [ProcessName] ASC)
);

