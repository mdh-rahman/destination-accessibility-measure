from pathlib import Path
import csv,json,shutil,hashlib,statistics,math
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--handoff',type=Path,required=True);args=ap.parse_args();r=args.root;h=args.handoff;h.mkdir(parents=True,exist_ok=True);out=h/'accessibility';out.mkdir(exist_ok=True)
specs={'community_social_recreation_nearest':'public_center_nearest','senior_center_nearest':'public_center_nearest','urgent_care_clinic_nearest':'urgent_care_nearest'}
qa=[];combined=[]
for sc,old in specs.items():
 for mode in ['drive','walk_transit']:
  p=r/'case-studies/austin/outputs/working'/sc/mode/'am_peak'
  rows=list(csv.DictReader((p/'accessibility.csv').open())); assert len(rows)==13189 and len({x['geography_id'] for x in rows})==13189
  matrix={}
  for x in csv.DictReader((p/'travel_matrix_subset.csv').open()):
   matrix[x['from_id']]=min(matrix.get(x['from_id'],math.inf),float(x['travel_time']))
  vals=[]
  for x in rows:
   v=float(x['access_value']) if x['access_value'] not in ['NA',''] else math.inf
   assert abs(v-matrix.get(x['geography_id'],math.inf))<1e-5 or v==matrix.get(x['geography_id'],math.inf)
   if math.isfinite(v): vals.append(v)
   combined.append(x)
  target=out/sc/mode;target.mkdir(parents=True,exist_ok=True)
  for f in ['accessibility.csv','run_manifest.json','qa_summary.csv']:shutil.copy2(p/f,target/f)
  oldp=r/'case-studies/austin/outputs/working'/old/mode/'am_peak/accessibility.csv'
  changed=None
  if oldp.exists():
   prev={x['geography_id']:x['access_value'] for x in csv.DictReader(oldp.open())};
   def number(v): return float(v) if v not in [None,'NA',''] else math.inf
   changed=sum(not (number(x['access_value'])==number(prev.get(x['geography_id'])) or abs(number(x['access_value'])-number(prev.get(x['geography_id'])))<1e-5) for x in rows)
  qa.append(dict(scenario=sc,mode=mode,origins=len(rows),reachable=len(vals),not_reached=len(rows)-len(vals),median_reachable_minutes=statistics.median(vals),minimum=min(vals),maximum=max(vals),changed_vs_legacy=changed,independent_OD_min_check='passed'))
with (out/'accessibility_results.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=combined[0]);w.writeheader();w.writerows(combined)
with (out/'validation_summary.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=qa[0]);w.writeheader();w.writerows(qa)
print(json.dumps(qa,indent=2))
