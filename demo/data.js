window.DATA = {
 "summary": {
  "rows": 3180146,
  "products": 100345,
  "creatives": 340906,
  "overall_ctr": 0.029651962852408564
 },
 "variance_split": {
  "creatives": 12568,
  "products": 3301,
  "min_imp": 500,
  "total_var": 0.00026310234147032514,
  "between_product_var": 0.0001465221253444974,
  "within_product_var_raw": 0.00011655928182112765,
  "sampling_noise_var": 3.3767790616326785e-05,
  "within_product_var_after_noise": 8.279149120480087e-05,
  "share_between_product": 0.638959550459132,
  "share_within_product_creative": 0.361040449540868
 },
 "early_call": {
  "min_total_imp": 3000,
  "products": 1760,
  "chance_level": 0.24203801406926412,
  "by_day": [
   {
    "days_observed": 1,
    "products": 1760,
    "leader_wins_later_days": 0.41704545454545455,
    "share_callable_at_95": 0.022727272727272728,
    "precision_when_called": 0.925,
    "median_imp_per_creative": 65.0
   },
   {
    "days_observed": 2,
    "products": 1760,
    "leader_wins_later_days": 0.45,
    "share_callable_at_95": 0.060227272727272727,
    "precision_when_called": 0.8490566037735849,
    "median_imp_per_creative": 144.0
   },
   {
    "days_observed": 3,
    "products": 1760,
    "leader_wins_later_days": 0.48125,
    "share_callable_at_95": 0.08863636363636364,
    "precision_when_called": 0.8525641025641025,
    "median_imp_per_creative": 225.0
   },
   {
    "days_observed": 4,
    "products": 1760,
    "leader_wins_later_days": 0.5113636363636364,
    "share_callable_at_95": 0.10909090909090909,
    "precision_when_called": 0.8802083333333334,
    "median_imp_per_creative": 310.0
   },
   {
    "days_observed": 7,
    "products": 1760,
    "leader_wins_later_days": 0.5056818181818182,
    "share_callable_at_95": 0.17045454545454544,
    "precision_when_called": 0.8166666666666667,
    "median_imp_per_creative": 574.0
   }
  ]
 },
 "budget_sim": {
  "products": 1760,
  "daily_impressions": 200,
  "days": 15,
  "reps": 3,
  "clicks_vs_oracle": {
   "uniform": 0.7533306649233081,
   "greedy_after_day1": 0.8265811619329794,
   "thompson": 0.8708725385635456,
   "oracle": 1.0
  },
  "lift_vs_uniform": {
   "uniform": 0.0,
   "greedy_after_day1": 0.09723551744323111,
   "thompson": 0.15602958848383475,
   "oracle": 0.32743833028727654
  },
  "shrink_factor": 0.7102951383301506
 },
 "confounding": {
  "pooled_spearman_imp_ctr": -0.04499552053937622,
  "mean_within_product_spearman": -0.04614685336828297,
  "products": 3076,
  "most_shown_is_best_ctr_share": 0.25097529258777634,
  "chance_level_for_3plus_creatives": 0.2691537917724524
 },
 "adset": {
  "product": "7c24b7cf",
  "creatives": [
   {
    "id": "ea640886",
    "imp": 13222,
    "clk": 703,
    "ctr": 0.053168960822870974,
    "lo": 0.04947261788623599,
    "hi": 0.05712487833661307
   },
   {
    "id": "80bc309c",
    "imp": 13313,
    "clk": 381,
    "ctr": 0.02861864343123263,
    "lo": 0.025919482985380535,
    "hi": 0.03158976905828723
   },
   {
    "id": "4a359522",
    "imp": 13152,
    "clk": 351,
    "ctr": 0.02668795620437956,
    "lo": 0.02406859616383326,
    "hi": 0.02958373726043052
   },
   {
    "id": "e7249264",
    "imp": 13019,
    "clk": 293,
    "ctr": 0.0225055687840848,
    "lo": 0.020095085338604088,
    "hi": 0.02519776380424351
   },
   {
    "id": "8dccf6f2",
    "imp": 13442,
    "clk": 160,
    "ctr": 0.01190299062639488,
    "lo": 0.010204031750501818,
    "hi": 0.01388085706746551
   }
  ]
 },
 "weekly": {
  "product": "cbe32217",
  "rows": [
   {
    "id": "4294dfb9",
    "imp_w1": 3531,
    "imp_w2": 8200,
    "ctr_w1": 0.017275559331634098,
    "ctr_w2": 0.011341463414634146,
    "z": -2.5901176250559663,
    "alert": true
   },
   {
    "id": "22ab33a6",
    "imp_w1": 3649,
    "imp_w2": 8366,
    "ctr_w1": 0.030419292956974514,
    "ctr_w2": 0.02318909873296677,
    "z": -2.3170176711482706,
    "alert": false
   },
   {
    "id": "b532db34",
    "imp_w1": 3674,
    "imp_w2": 8308,
    "ctr_w1": 0.014153511159499184,
    "ctr_w2": 0.01059220028887819,
    "z": -1.6726913717511886,
    "alert": false
   },
   {
    "id": "74eb2c98",
    "imp_w1": 3641,
    "imp_w2": 8174,
    "ctr_w1": 0.020049436967865972,
    "ctr_w2": 0.01578174700269146,
    "z": -1.652302207588592,
    "alert": false
   }
  ]
 }
};
