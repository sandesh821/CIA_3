CREATE PROCEDURE [logs].[usp_InsertPerfMetrics](
@ProcessName varchar(50),
@PID bigint,
@PPID bigint,
@MF_ResidentSetSize bigint,
@MF_VirtualMemorySize bigint,
@MF_Shared bigint,
@MF_TextResidentSet bigint,
@MF_DataResidentSet bigint,
@MF_Dirty bigint,
@CpuPercentage float,
@CpuNum bigint,
@CpuTimes float)
AS
BEGIN
	SET NOCOUNT ON;

	INSERT INTO [logs].[perfMetrics]
			   ([ProcessName]
			   ,[PID]
			   ,[PPID]
			   ,[MF_ResidentSetSize]
			   ,[MF_VirtualMemorySize]
			   ,[MF_Shared]
			   ,[MF_TextResidentSet]
			   ,[MF_DataResidentSet]
			   ,[MF_Dirty]
			   ,[CpuPercentage]
			   ,[CpuNum]
			   ,[CpuTimes])
		 VALUES
			   (@ProcessName
			   ,@PID
			   ,@PPID
			   ,@MF_ResidentSetSize
			   ,@MF_VirtualMemorySize
			   ,@MF_Shared
			   ,@MF_TextResidentSet
			   ,@MF_DataResidentSet
			   ,@MF_Dirty
			   ,@CpuPercentage
			   ,@CpuNum
			   ,@CpuTimes)

END