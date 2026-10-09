import unittest
import numpy as np
import pandas as pd
from analysis import make_features,rolling_evaluate,ROOT
class Tests(unittest.TestCase):
    def test_lags_use_past(self):
        f=make_features(pd.DataFrame({'year':range(2000,2010),'co2':range(10)}))
        row=f[f.year==2005].iloc[0]
        self.assertEqual(row.lag1,4);self.assertEqual(row.lag3,2)
    def test_year_gap_rejected(self):
        with self.assertRaises(ValueError):make_features(pd.DataFrame({'year':[2000,2002],'co2':[1,2]}))
    def test_future_change_does_not_change_past_forecast(self):
        d=pd.read_csv(ROOT/'data/cameroon_emissions.csv');a=rolling_evaluate(make_features(d),[2015])
        d.loc[d.year>=2016,'co2']=9999
        b=rolling_evaluate(make_features(d),[2015])
        np.testing.assert_allclose(a.prediction_mtco2,b.prediction_mtco2)
        self.assertTrue((a.train_last_year<a.year).all())
