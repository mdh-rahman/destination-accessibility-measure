#!/usr/bin/env python3
"""Build a dated team data package without rerouting or changing published results.
Python standard library; R sf/yaml/jsonlite required for inventory export.
"""
import argparse,csv,json,hashlib,shutil,subprocess
from pathlib import Path
from datetime import datetime,timezone

def write_csv(path,rows,fields=None):
 rows=list(rows)
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();r=a.root.resolve();o=a.output.resolve()
 if o.exists():raise SystemExit('Output already exists. Use a new dated snapshot; never overwrite a shared release.')
 for d in ['destinations','accessibility','demographics','geography']: (o/d).mkdir(parents=True,exist_ok=True)
 web=r/'site/austin-explorer';sources={}
 def copy(src,dst):
  p=r/src;target=o/dst;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);sources[dst]={'source_path':src,'source_sha256':sha(p)}
 subprocess.run(['Rscript',str(Path(__file__).with_name('export_inventories.R')),str(r),str(o)],check=True)
 for item in json.loads((o/'destinations/inventory_manifest.json').read_text()).values():
  source=r/item['source_path']; sources[item['source_path']]={'source_path':item['source_path'],'source_sha256':sha(source),'source_md5':hashlib.md5(source.read_bytes()).hexdigest()}
 copy('case-studies/austin/config/accessibility.yml','accessibility/analysis_configuration.yml')
 for n in ['h8-grid','austin-full-purpose','county-boundaries','metro-boundary','census-block-groups']:
  copy('site/austin-explorer/data/'+n+'.geojson','geography/'+n+'.geojson')
 grid=json.loads((web/'data/h8-grid.geojson').read_text());ids=[f['properties']['h3_id'] for f in grid['features']];regions=[f['properties']['region'] for f in grid['features']]
 assert len(ids)==len(set(ids))
 pop=json.loads((web/'data/population/population.json').read_text());assert pop['h3']['h3_id']==ids
 fields=list(pop['h3']);assert all(len(v)==len(ids) for v in pop['h3'].values())
 write_csv(o/'demographics/h3_population_counts.csv',({**{k:pop['h3'][k][i] for k in fields},'in_austin':regions[i]=='austin'} for i in range(len(ids))))
 write_csv(o/'demographics/population_groups.csv',pop['groups'])
 for geo in ['block_groups','tracts']:
  copy(f'population-access/output/demographic-review/austin_metro_demographics_{geo}.csv',f'demographics/acs2024_{geo}.csv')
 copy('population-access/output/demographic-review/variable_dictionary.csv','demographics/acs_variable_dictionary.csv')
 copy('case-studies/austin/data/processed/population_access/block_group_h8_crosswalk.csv','demographics/block_group_h8_crosswalk.csv')
 copy('population-access/output/equity-review/group_comparisons.csv','accessibility/group_comparisons.csv')
 copy('population-access/output/equity-review/quality_checks.csv','accessibility/quality_checks.csv')
 copy('site/austin-explorer/population-review/manifest.json','accessibility/equity_source_manifest.json')
 copy('site/austin-explorer/data/population/equity-summaries.json','accessibility/dashboard_equity_summaries.json')
 copy('site/austin-explorer/data/catalog.json','accessibility/dashboard_catalog.json')
 source_manifests={};definitions=[];nrows=0;seriescount=0
 with (o/'accessibility/accessibility_results.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['h3_id','in_austin','scenario','destination','mode','period','measure_id','value','unit','direction','result_status'])
  for scenario in json.loads((web/'data/catalog.json').read_text())['scenarios']:
   for key,filename in scenario['files'].items():
    p=web/filename;d=json.loads(p.read_text());sources[filename]={'source_path':str(p.relative_to(r)),'source_sha256':sha(p)}
    manifest=r/'case-studies/austin/outputs/working'/d['scenario']/d['mode']/d['period']/'run_manifest.json'
    if manifest.exists():source_manifests[key+'__'+d['scenario']]=json.loads(manifest.read_text())
    for s in d['series']:
     assert len(s['values'])==len(ids)
     seriescount+=1;definitions.append({'scenario':d['scenario'],'destination':scenario['destination'],'mode':d['mode'],'period':d['period'],'measure_id':s['id'],'label':s['label'],'unit':s['unit'],'direction':s['direction']})
     for i,v in enumerate(s['values']):
      status='modeled' if v is not None else ('incomplete_basket' if d['scenario']=='essential_destinations' else 'not_reached_within_model' if s['unit']=='minutes' else 'unavailable')
      w.writerow([ids[i],regions[i]=='austin',d['scenario'],scenario['destination'],d['mode'],d['period'],s['id'],v,s['unit'],s['direction'],status]);nrows+=1
 write_csv(o/'accessibility/measure_dictionary.csv',definitions)
 (o/'accessibility/run_manifests.json').write_text(json.dumps(source_manifests,indent=2))
 for filename in ['README.txt','analyze_shared_data.py']:
  shutil.copy2(Path(__file__).with_name(filename),o/filename)
 files=[{'path':str(p.relative_to(o)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(o.rglob('*')) if p.is_file()]
 manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'repository':'https://github.com/mdh-rahman/destination-accessibility-measure','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip(),'scope':'Team snapshot; includes source-derived data, not cleared for public redistribution','origins':len(ids),'austin_origins':regions.count('austin'),'series':seriescount,'accessibility_rows':nrows,'population_groups_excluding_reference':len(pop['groups'])-1,'files':files,'source_files':sources}
 (o/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({k:v for k,v in manifest.items() if k not in ['files','source_files']},indent=2))
if __name__=='__main__':main()
