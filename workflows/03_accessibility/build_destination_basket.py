#!/usr/bin/env python3
"""Build an equal-category nearest-destination basket and package it for the dashboard.
Run after export_dashboard_data.py. Requires pandas and numpy.
"""
import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
BASKET={'grocery_nearest':'Grocery','childcare_nearest':'Childcare','pharmacy_nearest':'Pharmacy','urgent_care_nearest':'Urgent care','hospital_nearest':'Hospital','park_nearest':'Park','library_nearest':'Library','public_center_nearest':'Public center'}
THRESHOLDS=[15,30,60]
def main():
 site=ROOT/'site/austin-explorer';working=ROOT/'case-studies/austin/outputs/working'
 ids=[f['properties']['h3_id'] for f in json.loads((site/'data/h8-grid.geojson').read_text())['features']]
 item={'id':'essential_destinations','destination':'Essential destinations · combined','short':'Essential destinations','measure':'aggregate','description':'Eight equally weighted destination types: grocery, childcare, pharmacy, urgent care, hospital, park, library and public center. Average is shown only when all eight have a modeled route. Reachable-type counts use one nearest facility per category. Jobs and park acreage remain separate.','source':'Existing reviewed destination inventories and peak travel-time outputs','modes':['drive','walk_transit'],'periods':['am_peak'],'files':{}}
 for mode in item['modes']:
  values=[];valid=[];sources=[]
  for scenario in BASKET:
   p=working/scenario/mode/'am_peak/accessibility.csv';meta=json.loads(p.with_name('run_manifest.json').read_text());assert meta['mode']==mode and meta['period']=='am_peak';assert meta['maximum_trip_minutes']==(60 if mode=='drive' else 90);f=pd.read_csv(p,dtype={'geography_id':str});assert f.geography_id.is_unique and len(f)==len(ids)
   assert set(f.geography_id)==set(ids) and (f.parameter_value==1).all()
   f=f.set_index('geography_id').reindex(ids)
   x=f.access_value.to_numpy(float); known=f.is_reachable.isin([True,False]).to_numpy() & (~f.is_reachable | np.isfinite(x)).to_numpy()
   x[~f.is_reachable.to_numpy(bool)]=np.nan
   values.append(x);valid.append(known);sources.append({'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  matrix=np.array(values).T;assert (matrix[np.isfinite(matrix)]>=0).all();known=np.array(valid).T.all(axis=1);reached=np.isfinite(matrix).sum(axis=1);complete=known&(reached==len(BASKET))
  mean=np.full(len(ids),np.nan);mean[complete]=matrix[complete].mean(axis=1)
  serial=lambda a:[float(v) if np.isfinite(v) else None for v in a]
  series=[{'id':'mean_nearest__8','label':'Average nearest-destination time','unit':'minutes','direction':'lower','values':serial(mean)}]
  table=pd.DataFrame({'geography_id':ids,'mode':mode,'period':'am_peak','categories_reached':reached,'complete_basket':complete,'mean_nearest_minutes':mean})
  for j,label in enumerate(BASKET):table[label+'_minutes']=matrix[:,j]
  for cutoff in THRESHOLDS:
   count=((matrix<=cutoff)&np.isfinite(matrix)).sum(axis=1).astype(float);count[~known]=np.nan
   series.append({'id':f'category_count__{cutoff}','label':f'Destination types within {cutoff} minutes','unit':'types','direction':'higher','values':serial(count)})
   table[f'types_within_{cutoff}_minutes']=count
  dest=working/'essential_destinations'/mode/'am_peak';dest.mkdir(parents=True,exist_ok=True);table.to_csv(dest/'origin_basket.csv',index=False)
  long=[]
  for cutoff in THRESHOLDS:
   for i,gid in enumerate(ids):long.append({'geography_id':gid,'scenario':'essential_destinations','destination':'essential_destinations','mode':mode,'period':'am_peak','measure':'cumulative_opportunities','opportunity_field':'category_count','parameter_name':'cutoff_minutes','parameter_value':cutoff,'access_value':table[f'types_within_{cutoff}_minutes'].iloc[i],'is_reachable':bool(known[i])})
  pd.DataFrame(long).to_csv(dest/'accessibility.csv',index=False)
  manifest={'maximum_trip_minutes':60 if mode=='drive' else 90,'basket':BASKET,'weights':'equal categories, 1/8 each','missing_rule':'No partial mean; any unreachable category makes the mean unavailable. Unknown input makes threshold counts unavailable.','thresholds_minutes':THRESHOLDS,'routing_limit_minutes':60 if mode=='drive' else 90,'inputs':sources,'origins':len(ids),'complete_baskets':int(complete.sum())}
  (dest/'run_manifest.json').write_text(json.dumps(manifest,indent=2))
  name=f'essential_destinations__{mode}__am_peak.json'
  payload={'scenario':item['id'],'mode':mode,'period':'am_peak','series':series,'basket':list(BASKET.values()),'nearest_times':[serial(row) for row in matrix],'categories_reached':reached.tolist(),'known':known.tolist(),'routing_limit_minutes':manifest['routing_limit_minutes']}
  (site/'data/results'/name).write_text(json.dumps(payload,separators=(',',':'),allow_nan=False));item['files'][f'{mode}:am_peak']='data/results/'+name
  print(mode,len(ids),'origins;',complete.sum(),'complete baskets')
 catpath=site/'data/catalog.json';catalog=json.loads(catpath.read_text());catalog['scenarios']=[item]+[s for s in catalog['scenarios'] if s['id']!=item['id']];catpath.write_text(json.dumps(catalog,indent=2))
if __name__=='__main__':main()
