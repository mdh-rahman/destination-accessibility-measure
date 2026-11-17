#!/usr/bin/env python3
"""Portable, standard-library example: validate a shared snapshot and summarize nearest groceries.
Set DAM_DATA_DIR to the local synced snapshot folder, or pass --data-dir.
No repository-specific paths and no routing dependencies are required.
"""
import argparse,csv,hashlib,json,os
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--data-dir',default=os.environ.get('DAM_DATA_DIR'));p.add_argument('--region',choices=['austin','metro'],default='austin');p.add_argument('--mode',choices=['drive','walk_transit'],default='drive');p.add_argument('--group',default='below_200_poverty');p.add_argument('--threshold',type=float,default=30);p.add_argument('--verify',action='store_true');a=p.parse_args()
 if not a.data_dir:p.error('Set DAM_DATA_DIR or supply --data-dir pointing to a dated shared snapshot.')
 root=Path(a.data_dir);manifest=json.loads((root/'manifest.json').read_text())
 if a.verify:
  for item in manifest['files']:
   h=hashlib.sha256()
   with (root/item['path']).open('rb') as f:
    for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
   if h.hexdigest()!=item['sha256']:raise ValueError('Checksum mismatch: '+item['path'])
  print('All snapshot file checksums verified.')
 with (root/'demographics/h3_population_counts.csv').open() as f:pop={x['h3_id']:x for x in csv.DictReader(f)}
 with (root/'demographics/population_groups.csv').open() as f:groups={x['group_id']:x for x in csv.DictReader(f)}
 if a.group not in groups:p.error('Unknown population group: '+a.group)
 vals=[];total=covered=unreached=0
 with (root/'accessibility/accessibility_results.csv').open() as f:
  for x in csv.DictReader(f):
   if x['scenario']!='grocery_nearest' or x['mode']!=a.mode or (a.region=='austin' and x['in_austin']!='True'):continue
   raw=pop[x['h3_id']][a.group];weight=float(raw) if raw else 0
   if weight<=0:continue
   value=float(x['value']) if x['value'] else float('inf');total+=weight;unreached+=weight if value==float('inf') else 0;covered+=weight if value<=a.threshold else 0;vals.append((value,weight))
 if not total:raise ValueError('No group population available.')
 accumulated=0;median=None
 for v,w in sorted(vals):
  accumulated+=w
  if accumulated>=total/2:median=v;break
 result={'region':a.region,'mode':a.mode,'group':a.group,'population_unit':groups[a.group]['unit'],'estimated_group_total':total,'nearest_grocery_coverage_threshold_minutes':a.threshold,'coverage_percent':100*covered/total,'not_reached_percent':100*unreached/total,'weighted_median_minutes':median if median!=float('inf') else None,'median_status':'not_reached_within_model' if median==float('inf') else 'modeled'}
 print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':main()
