"""Package the current equity review into the dashboard; does not publish to hosting.
Run after build_equity_review.py. Keeps browser selectors and population summaries aligned.
"""
import json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[3];site=Path(__file__).resolve().parents[1]
out=root/'population-access/output/equity-review';review=site/'population-review';review.mkdir(exist_ok=True)
html=(out/'review.html').read_text();d=json.loads(html.split('<script id="dataset" type="application/json">')[1].split('</script>')[0])
ids=[f['properties']['h3_id'] for f in json.loads((site/'data/h8-grid.geojson').read_text())['features']];assert ids==d['ids']
for name in ['review.html','group_comparisons.csv','quality_checks.csv','manifest.json','README.txt']:shutil.copy2(out/name,review/name)
groups=[{'group_id':'total_population','label':'All residents','unit':'person','denominator':'total_population'}]+[{'group_id':g['id'],'label':g['label'],'unit':{'people':'person','households':'household','families':'family','workers':'worker'}[g['unit']],'denominator':g['reference']} for g in d['groups']]
pop={'groups':groups,'h3':{'h3_id':ids,**d['population']},'outcomes':[]}
(site/'data/population/population.json').write_text(json.dumps(pop,separators=(',',':')))
compact={s['key']:{'time':s['time'],'cap':s['cap'],'regions':{region:{'threshold':v['threshold'],'policy':v['policy'],'groups':{g:{k:x for k,x in st.items() if k!='curve'} for g,st in v['groups'].items()},'references':{g:{k:x for k,x in st.items() if k!='curve'} for g,st in v['references'].items()}} for region,v in s['regions'].items()}} for s in d['series']}
(site/'data/population/equity-summaries.json').write_text(json.dumps(compact,separators=(',',':')))
print('Packaged equity charts, 12 population groups and',len(compact),'series; no hosting changes.')
