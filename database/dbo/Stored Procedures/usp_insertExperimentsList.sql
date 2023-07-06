-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2022
-- Modified Date : 29th March 2023 ( change : added quantile column)
-- Description: Insert experiment set transformation details
-- =============================================
CREATE PROCEDURE [dbo].[usp_insertExperimentsList] 
@ExperimentSetID int,
@ExperimentTag [varchar] (100),
@Algorithm [varchar] (100),
@PastCovariates [varchar] (1000),
@FutureCovariates [varchar] (1000),
@Entity [varchar] (100),
@TrainStart [varchar] (100),
@TrainEnd [varchar] (100),
@ValStart [varchar] (100),
@ValEnd [varchar] (100),
@TestStart [varchar] (100),
@TestEnd [varchar] (100),
@quantileList [varchar] (100)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
  BEGIN
     INSERT INTO [dbo].[experimentsList]
           (
			ExperimentSetID,
			ExperimentTag ,
			[Algorithm] ,
			PastCovariates,
			FutureCovariates,
			Entity ,
			TrainStart ,
			TrainEnd ,
			ValStart ,
			ValEnd ,
			TestStart ,
			TestEnd,
			quantileList  )
     VALUES
           (@ExperimentSetID,
			@ExperimentTag ,
			@Algorithm ,
			@PastCovariates,
			@FutureCovariates,
			@Entity ,
			@TrainStart ,
			@TrainEnd ,
			@ValStart ,
			@ValEnd ,
			@TestStart ,
			@TestEnd,
			@quantileList  )
  END
END