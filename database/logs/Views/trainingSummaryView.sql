CREATE VIEW [logs].[trainingSummaryView] 
AS 
with cte as (
SELECT 
[logs].[statusTracker].[Status] as [Training Status],
CASE
WHEN 
[logs].[childRunTracker].[ModelName] != 'DeepMC' 
THEN 
    CASE
    WHEN [logs].[statusTracker].[Status] = 'prepare_training' THEN 3
    WHEN [logs].[statusTracker].[Status] = 'training_start' THEN 91
    WHEN [logs].[statusTracker].[Status] = 'training_end' THEN 100
    ELSE
    ((ROW_NUMBER() OVER (PARTITION BY [logs].[statusTracker].[AMLRunId] ORDER BY [logs].[statusTracker].[CreatedOn]))*1.0/(([logs].[statusTracker].[N_Trials]*4)+5))*100
    END
WHEN 
[logs].[childRunTracker].[ModelName] = 'DeepMC' THEN
CASE
    WHEN [logs].[statusTracker].[Status]='prepare_training' THEN 10
    WHEN [logs].[statusTracker].[Status]='training_start' THEN 20
    WHEN [logs].[statusTracker].[Status]='training_end' THEN 100
    ELSE     (((SUM(CASE WHEN [logs].[statusTracker].[Status]='finished_hpt' THEN 1 ELSE 0 END) 
    OVER (PARTITION BY [logs].[statusTracker].[AMLRunId] ORDER BY [logs].[statusTracker].[CreatedOn])*1.0/[logs].[statusTracker].[Horizon])*70)+20)
    END
    END
as progress_pcs,
[logs].[statusTracker].[TotalEpoch] as [Pending Epochs],
[logs].[statusTracker].[AMLRunId], 
[logs].[statusTracker].[InternalModelNumber],
    CASE 
    WHEN [logs].[statusTracker].[InternalModelNumber] = -1 THEN 'Operational Model'
    ELSE CONCAT('Internal Model Number ',[logs].[statusTracker].[InternalModelNumber])
    END as [Model Type], [logs].[statusTracker].[CreatedOn] as [Created On],
[logs].[statusTracker].[N_Trials],
[logs].[statusTracker].[Trial_Number],
[logs].[statusTracker].[ChildAMLRunId],
[logs].[statusTracker].[Horizon],
[logs].[runTracker].[ExperimentSet] as  [Experiment Set Name],
[logs].[runTracker].[InternalRunID],
[logs].[runTracker].[RunStatus] as [Experiment Run Status],
[logs].[runTracker].[CreatedOn] as [CreatedOn_runTracker],
[logs].[runTracker].[StartDateTime] as [StartDateTime_runTracker],
[logs].[runTracker].[EndDateTime] as [EndDateTime_runTracker],   
[logs].[childRunTracker].[Experiment] as [Experiment Name],
[logs].[childRunTracker].[ModelName] as [Model Name],
[logs].[childRunTracker].[CreatedOn] as [CreatedOn_childRunTracker],
[logs].[childRunTracker].[StartDateTime] as [StartDateTime_childRunTracker],
[logs].[childRunTracker].[EndDateTime] as [EndDateTime_childRunTracker] FROM 
[logs].[statusTracker] 
RIGHT JOIN [logs].[runTracker]
ON [logs].[statusTracker].[AMLRunId] = [logs].[runTracker].[AMLRunId] 
LEFT JOIN [logs].[childRunTracker]
ON [logs].[runTracker].[InternalRunID] = [logs].[childRunTracker].[InternalRunID]
AND 
[logs].[statusTracker].[ChildAMLRunId] = [logs].[childRunTracker].[ChildAMLRunId]
WHERE [logs].[statusTracker].[Status] != 'prepare_training' AND [logs].[childRunTracker].[ChildAMLRunId] is NOT NULL
 ORDER BY [logs].[statusTracker].[CreatedOn] Desc OFFSET 0 ROWS
), cte2 as (SELECT 
CASE WHEN [InternalModelNumber] = -1 
THEN 
MAX(progress_pcs) OVER (PARTITION BY [AMLRunId]) ELSE 0 END as progress_pct,
*,
CASE
     WHEN [Experiment Run Status] != 'Failed' AND [EndDateTime_childRunTracker] iS NULL
    THEN
    DATEDIFF(ss,[StartDateTime_childRunTracker],CURRENT_TIMESTAMP)
    ELSE
    DATEDIFF(ss,[StartDateTime_childRunTracker],[EndDateTime_childRunTracker])
    END as [seconds_diff] FROM cte) SELECT 
   [Training Status]
      ,[progress_pct]
      ,[Pending Epochs]
      ,[AMLRunId]
      ,[InternalModelNumber]
      ,[Model Type]
      ,[Created On]
      ,[N_Trials]
      ,[Trial_Number]
      ,[ChildAMLRunId]
      ,[Horizon]
      ,[Experiment Set Name]
      ,[InternalRunID]
      ,[Experiment Run Status]
      ,[CreatedOn_runTracker]
      ,[StartDateTime_runTracker]
      ,[EndDateTime_runTracker]
      ,[Experiment Name]
      ,[Model Name]
      ,[CreatedOn_childRunTracker]
      ,[StartDateTime_childRunTracker]
      ,[EndDateTime_childRunTracker]
      ,
    IIF((AVG([seconds_diff]) OVER (PARTITION BY [Experiment Set Name],[Model Name])) is NULL,NULL,
    CONCAT(FORMAT(AVG([seconds_diff]) OVER (PARTITION BY [Experiment Set Name],[Model Name])/3600,'00'),':',
    FORMAT((AVG([seconds_diff]) OVER (PARTITION BY [Experiment Set Name],[Model Name])%3600)/60,'00'),':',
    FORMAT(((AVG([seconds_diff]) OVER (PARTITION BY [Experiment Set Name],[Model Name]))%3600)%60,'00')))
    as [Average Runtime For Model],     IIF((AVG([seconds_diff]) OVER (PARTITION BY [Experiment Set Name],[Model Name])) is NULL,NULL,CONCAT(FORMAT([seconds_diff]/3600,'00'),':',
    FORMAT(([seconds_diff]%3600)/60,'00'),':',
    FORMAT(([seconds_diff]%3600)%60,'00')))      as [Experiment Runtime]
FROM cte2
WHERE [InternalModelNumber] = -1