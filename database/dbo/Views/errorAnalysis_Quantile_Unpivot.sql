CREATE view [dbo].[errorAnalysis_Quantile_Unpivot] as SELECT t.*,
    'Quantile' as key_value,
     CASE WHEN j.[key] = 'Actual' THEN 'Actual' ELSE j.[key] END AS percentile_key,
     CASE WHEN j.[key] = 'Actual' THEN CAST(t.Actual AS VARCHAR(MAX)) ELSE j.value END AS percentile_value
from [dbo].[errorAnalysis] t
cross apply 
openjson( REPLACE(t.quantile, '''', '"')) j
UNION ALL
SELECT t.*,
    'Quantile' as key_value,
     'Actual' AS percentile_key,
     CAST(t.Actual AS VARCHAR(MAX)) AS percentile_value
FROM [dbo].[errorAnalysis] t
union all
select t.*,
    'BiasCorrection' as key_value,
    case when j.[key]='BiasCorrection' then 'BiasCorrection' else j.[key] end as percentile_key,
    case when j.[key]='BiasCorrection' then cast(t.BiasCorrection as varchar(max)) else j.value end as percentile_value
from [dbo].[errorAnalysis] t
cross apply
openjson( REPLACE(t.BiasCorrection, '''', '"'))  j
union all
SELECT t.*,
    'BiasCorrection' as key_value,
     'Actual' AS percentile_key,
     CAST(t.Actual AS VARCHAR(MAX)) AS percentile_value
FROM [dbo].[errorAnalysis] t
union all
SELECT t.*,
    'BiasCorrection' as key_value,
    'Prediction' as percentile_key,
    CAST(t.prediction as VARCHAR(max)) as percentile_value
FROM [dbo].[errorAnalysis] t
union all
SELECT t.*,
    'Quantile' as key_value,
    'Prediction' as percentile_key,
    CAST(t.prediction as VARCHAR(max)) as percentile_value
FROM [dbo].[errorAnalysis] t