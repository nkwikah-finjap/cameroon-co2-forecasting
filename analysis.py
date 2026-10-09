"""Leakage-aware, rolling one-year-ahead forecasting of Cameroon CO2 emissions."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent

def make_features(d,lags=3):
    d=d.sort_values('year').copy()
    if d.year.duplicated().any() or not np.all(np.diff(d.year)==1):raise ValueError('Need unique consecutive years')
    if d.co2.isna().any():raise ValueError('Missing emissions')
    for k in range(1,lags+1):d[f'lag{k}']=d.co2.shift(k)
    return d.dropna(subset=[f'lag{k}' for k in range(1,lags+1)])

def models():
    return {'ridge':make_pipeline(StandardScaler(),Ridge(alpha=10.)),
        'random_forest':RandomForestRegressor(n_estimators=200,max_depth=3,min_samples_leaf=3,random_state=42,n_jobs=1)}

def rolling_evaluate(features,years):
    rows=[];cols=['lag1','lag2','lag3']
    for year in years:
        train=features[features.year<year];test=features[features.year==year]
        if len(train)<15 or len(test)!=1:raise ValueError('Insufficient training or invalid target')
        actual=float(test.co2.iloc[0]);last=float(test.lag1.iloc[0])
        preds={'persistence':last,'local_drift':max(0.,last+(last-float(test.lag3.iloc[0]))/2.)}
        for name,model in models().items():
            model.fit(train[cols],train.co2);preds[name]=max(0.,float(model.predict(test[cols])[0]))
        for name,pred in preds.items():rows.append({'year':int(year),'model':name,'actual_mtco2':actual,'prediction_mtco2':pred,'train_last_year':int(train.year.max())})
    return pd.DataFrame(rows)

def scores(rows):
    result=[]
    for model,g in rows.groupby('model'):
        error=g.prediction_mtco2-g.actual_mtco2
        result.append({'model':model,'MAE_mtco2':float(np.abs(error).mean()),'RMSE_mtco2':float(np.sqrt((error**2).mean())),'n_years':len(g)})
    return pd.DataFrame(result).sort_values('RMSE_mtco2')

def forecast(d,features,chosen,steps=6):
    history=d.co2.to_list();years=[];preds=[];model=None
    if chosen in models():
        model=models()[chosen];model.fit(features[['lag1','lag2','lag3']],features.co2)
    for k in range(1,steps+1):
        if chosen=='persistence':pred=history[-1]
        elif chosen=='local_drift':pred=history[-1]+(history[-1]-history[-3])/2.
        else:pred=float(model.predict(pd.DataFrame([[history[-1],history[-2],history[-3]]],columns=['lag1','lag2','lag3']))[0])
        pred=max(0.,pred);history.append(pred);years.append(int(d.year.max())+k);preds.append(pred)
    return pd.DataFrame({'year':years,'forecast_mtco2':preds,'model':chosen})

def run():
    out=ROOT/'results';out.mkdir(exist_ok=True)
    d=pd.read_csv(ROOT/'data/cameroon_emissions.csv');f=make_features(d)
    # Choice uses validation 2005–2014 only; test 2015–2024 never selects the model.
    validation=rolling_evaluate(f,range(2005,2015));vs=scores(validation)
    chosen=vs.iloc[0].model
    test=rolling_evaluate(f,range(2015,2025));ts=scores(test)
    validation.to_csv(out/'validation_predictions.csv',index=False);vs.to_csv(out/'validation_scores.csv',index=False)
    test.to_csv(out/'test_predictions.csv',index=False);ts.to_csv(out/'test_scores.csv',index=False)
    future=forecast(d,f,chosen);future.to_csv(out/'forecasts_2025_2030.csv',index=False)
    fig,axes=plt.subplots(2,1,figsize=(10,7))
    axes[0].plot(d.year,d.co2,color='#126a8a',label='Observed annual fossil/industry emissions')
    axes[0].plot([int(d.year.max())]+future.year.to_list(),[float(d.co2.iloc[-1])]+future.forecast_mtco2.to_list(),'--o',color='#ce6b32',label=f'Forecast: {chosen}')
    axes[0].set(ylabel='Million tonnes CO₂',title='Cameroon emissions: observations through 2024; forecasts are estimates')
    for name,g in test.groupby('model'):axes[1].plot(g.year,g.prediction_mtco2,marker='.',label=name)
    actual=test[test.model=='persistence'];axes[1].plot(actual.year,actual.actual_mtco2,'k-o',label='Observed')
    axes[1].set(xlabel='Year',ylabel='Million tonnes CO₂',title='Rolling one-year forecasts: test period 2015–2024')
    for ax in axes:ax.legend(fontsize=8);ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(out/'forecast_and_backtest.png',dpi=160);plt.close(fig)
    metrics={'country':'Cameroon','unit':'Mt CO2 / year','first_year':int(d.year.min()),'last_observed_year':int(d.year.max()),'observed_years':len(d),
        'validation_years':[2005,2014],'test_years':[2015,2024],'selected_on_validation':chosen,
        'selected_test_scores':ts[ts.model==chosen].iloc[0].to_dict(),'all_test_scores':ts.to_dict(orient='records'),
        'forecast_warning':'2025–2030 values are recursive estimates, not observations. One-step backtest does not validate six-year accuracy.'}
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2));return metrics
if __name__=='__main__':print(json.dumps(run(),indent=2))
