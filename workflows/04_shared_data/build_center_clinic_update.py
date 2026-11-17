#!/usr/bin/env python3
import argparse,csv,json,shutil,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone
ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();r=a.root;o=a.output
assert not o.exists(),'Never overwrite a released snapshot'
shutil.copytree(a.baseline,o)
def rows(p):return list(csv.DictReader(p.open()))
def write(p,x):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=x[0]);w.writeheader();w.writerows(x)
res=rows(o/'accessibility/accessibility_results.csv');dic=rows(o/'accessibility/measure_dictionary.csv');area={x['h3_id']:x['in_austin'] for x in res};n=len(area)
for sc,inv,label in [('community_social_recreation_nearest','community_social_recreation','Community/social/recreation centers'),('senior_center_nearest','senior_centers','Senior centers'),('urgent_care_clinic_nearest','urgent_care_clinics','Urgent care/clinics')]:
 for ext in ['gpkg','csv']:shutil.copy2(r/f'case-studies/austin/data/destinations/center_clinic_update_2026-11-17/{inv}.{ext}',o/f'destinations/{inv}.{ext}')
 for mode in ['drive','walk_transit']:
  p=r/'case-studies/austin/outputs/working'/sc/mode/'am_peak';data=rows(p/'accessibility.csv');assert len(data)==n
  for x in data:
   v=x['access_value'];res.append(dict(h3_id=x['geography_id'],in_austin=area[x['geography_id']],scenario=sc,destination=label,mode=mode,period='am_peak',measure_id='facility_count__1',value='' if v=='NA' else v,unit='minutes',direction='lower',result_status='modeled' if v!='NA' else 'not_reached_within_model'))
  dic.append(dict(scenario=sc,destination=label,mode=mode,period='am_peak',measure_id='facility_count__1',label='Travel time to nearest '+label.lower(),unit='minutes',direction='lower'))
  target=o/'accessibility/update_run_manifests';target.mkdir(exist_ok=True);shutil.copy2(p/'run_manifest.json',target/f'{sc}__{mode}.json')
write(o/'accessibility/accessibility_results.csv',res);write(o/'accessibility/measure_dictionary.csv',dic)
shutil.copy2(r/'case-studies/austin/config/accessibility.yml',o/'accessibility/analysis_configuration.yml')
(o/'UPDATE_2026-11-17.txt').write_text('Six new AM nearest-destination series appended. Legacy series and equity/dashboard summaries are retained as historical November 3 results; they do not incorporate new inventories. Use the three new scenario names. All profiles and derived scores must be rebuilt downstream. Old public_center includes senior and Luling records; old urgent_care uses NPPES. New clinic definition is broader. Source code commit below applies to update, not all historical runs.\n')
m=json.loads((o/'manifest.json').read_text());m['baseline_source_commit']=m['source_commit'];m['created_utc']=datetime.now(timezone.utc).isoformat();m['source_commit']=subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD'],text=True).strip();m['series']=len(dic);m['accessibility_rows']=len(res);m['update_note']='Append six recalculated series; retain legacy series and summaries with baseline provenance';m['files']=[dict(path=str(p.relative_to(o)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(o.rglob('*')) if p.is_file() and p!=o/'manifest.json'];(o/'manifest.json').write_text(json.dumps(m,indent=2));print('Built',o,len(dic),'series',len(res),'rows')
