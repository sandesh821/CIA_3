#Copyright (c) Microsoft. All rights reserved.
import optuna

def optimize(Objectivefunc,n_trials, datasetPath,trainParams):
    '''
    Objectivefunc: objective should be a predefined function in every model class file
    n_trials: number of trials for optimizing the params
    '''
    objectiveFunc = lambda trial: Objectivefunc(trial, datasetPath,trainParams, n_trials)

    # We use the multivariate TPE sampler.
    sampler = optuna.samplers.TPESampler(multivariate=True)
 
    study = optuna.create_study(sampler=sampler)

    study.optimize(objectiveFunc, n_trials=n_trials)
    print(study.trials_dataframe())
    return study.best_params

def optimizeInternalModels(Objectivefunc,n_trials,classObj,path,pred_idx,horizon):
    '''
    Objectivefunc: objective should be a predefined function in every model class file
    n_trials: number of trials for optimizing the params
    '''
    objectiveFunc = lambda trial: Objectivefunc(trial,classObj,path,n_trials,pred_idx,horizon)

    # We use the multivariate TPE sampler.
    sampler = optuna.samplers.TPESampler(multivariate=True)
 
    study = optuna.create_study(sampler=sampler)

    study.optimize(objectiveFunc, n_trials=n_trials)
    print(study.trials_dataframe())
    return study.best_params