"""Create broad ACS review tables without changing accessibility or website inputs.

Usage: python export_demographic_review.py /path/to/destination-accessibility-measure
Requires pandas, numpy, requests and R with sf/jsonlite. Reuses the validated
block-to-H3 crosswalk from prepare_demographics.R; does not silently refresh it.
"""
import json, sys, subprocess, hashlib, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from urllib.request import urlopen
from urllib.parse import urlencode

ROOT = Path(sys.argv[1]).resolve()
OUT = ROOT / 'population-access/output/demographic-review'
RAW = ROOT / 'case-studies/austin/data/raw/population_access/review_expanded'
PROC = ROOT / 'case-studies/austin/data/processed/population_access'
for p in (OUT, RAW): p.mkdir(parents=True, exist_ok=True)
COUNTIES = {'021':'Bastrop','055':'Caldwell','209':'Hays','453':'Travis','491':'Williamson'}
# Evaluate only the existing group-definition expression, not the production pipeline.
r_code = '''args<-commandArgs(TRUE); root<-args[1]; out<-args[2]
for(e in parse(file.path(root,"population-access/scripts/prepare_demographics.R"))) {
 if(is.call(e)&&identical(e[[1]],as.name("<-"))&&identical(e[[2]],as.name("groups"))) eval(e)
}
jsonlite::write_json(groups,file.path(out,"base_groups.json"),auto_unbox=TRUE)
suppressPackageStartupMessages(library(sf))
for(kind in c("block_group","tract")) {
 f<-if(kind=="block_group") "block_group_demographics.gpkg" else "tract_disability.gpkg"
 x<-st_read(file.path(root,"case-studies/austin/data/processed/population_access",f),quiet=TRUE)
 xy<-st_coordinates(st_transform(st_point_on_surface(st_transform(x,5070)),4326))
 write.csv(data.frame(geoid=x$GEOID,longitude=xy[,1],latitude=xy[,2],area_sq_km=as.numeric(st_area(st_transform(x,5070)))/1e6),file.path(out,paste0(kind,"_locations.csv")),row.names=FALSE)
}
h<-st_read(file.path(root,"site/austin-explorer/data/h8-grid.geojson"),quiet=TRUE)
xy<-st_coordinates(st_transform(st_centroid(st_transform(h,5070)),4326))
write.csv(data.frame(h3_id=h$h3_id,region=h$region,longitude=xy[,1],latitude=xy[,2],area_sq_km=as.numeric(st_area(st_transform(h,5070)))/1e6),file.path(out,"h3_locations.csv"),row.names=FALSE)
'''
subprocess.run(['Rscript','-e',r_code,str(ROOT),str(RAW)],check=True)
groups=json.loads((RAW/'base_groups.json').read_text())
def seq(table, nums): return [f'{table}_{n:03d}' for n in nums]
def add(key,label,unit,den,table,nums,note=''):
    groups[key]={'label':label,'unit':unit,'denominator':den,'codes':seq(table,nums),'note':note}
add('children_under_15','Children under 15','person','total_population','B01001',[3,4,5,27,28,29])
add('adults_75_plus','Adults age 75 and older','person','total_population','B01001',[23,24,25,47,48,49])
add('total_households','Total households','household','total_households','B25003',[1])
add('renter_households','Renter households','household','total_households','B25003',[3])
add('owner_households','Owner households','household','total_households','B25003',[2])
add('families_with_own_children','Families with own children under 18','family','families_with_own_children','B11003',[3,10,16])
add('single_parent_families','Families with own children under 18, no spouse present','family','families_with_own_children','B11003',[10,16], 'ACS no-spouse-present definition; unmarried partners may be present. Not all households with children.')
add('civilian_labor_force','Civilian labor force age 16+','person','civilian_labor_force','B23025',[3])
add('unemployed','Unemployed civilian labor force','person','civilian_labor_force','B23025',[5])
add('foreign_born','Foreign-born residents','person','total_population','B05002',[13])
add('noncitizens','Residents who are not US citizens','person','total_population','B05002',[21], 'Citizenship is not refugee, undocumented, or non-permanent-resident status.')
add('foreign_born_entered_2010_plus','Foreign-born residents entering US in 2010 or later','person','foreign_born','B05005',[4], '2010+ is the available table interval; not equivalent to the Canadian 2016-2021 recent-immigrant category.')
for key in ['foreign_born','noncitizens','foreign_born_entered_2010_plus']:
    groups[key]['geography']='tract'
add('commuting_workers','Workers age 16+ not working from home','person','commuting_workers','B08303',[1])
add('commute_60_plus','Workers commuting 60 minutes or longer','person','commuting_workers','B08303',[12,13], 'Includes exactly 60 minutes; an observed commute outcome, not modeled accessibility.')
add('adults_25_plus','Residents age 25+','person','adults_25_plus','B15003',[1])
add('less_than_high_school','Adults age 25+ without high school completion','person','adults_25_plus','B15003',range(2,17))
add('crowded_households','Households with more than one occupant per room','household','total_households','B25014',[5,6,7,11,12,13], 'Crowding proxy, not equivalent to Canadian housing suitability or housing repair status.')
add('housing_cost_known','Households with computed housing-cost-to-income ratio','household','housing_cost_known','B25070',range(2,11))
groups['housing_cost_known']['codes'] += seq('B25091',list(range(3,12))+list(range(14,23)))
add('housing_cost_30_plus','Households spending 30%+ of income on housing','household','housing_cost_known','B25070',range(7,11))
groups['housing_cost_30_plus']['codes'] += seq('B25091',list(range(8,12))+list(range(19,23)))
add('housing_cost_50_plus','Households spending 50%+ of income on housing','household','housing_cost_known','B25070',[10])
groups['housing_cost_50_plus']['codes'] += seq('B25091',[11,22])
for key,g in groups.items():
    for field in ('codes','subtract'):
        if isinstance(g.get(field),str):g[field]=[g[field]]
    g.setdefault('note','')
    if key=='below_200_poverty':g['note']='Below 2.00 income-to-poverty ratio; US threshold, not Canadian LICO.'

def fetch(job):
    county,geo,tables=job
    digest=hashlib.sha256(','.join(tables).encode()).hexdigest()[:10]
    path=RAW/f'acs2024_{geo}_48{county}_{digest}.json'
    params={'table_ids':','.join(tables),'geo_ids':f'{geo}|05000US48{county}'}
    if not path.exists():
        for attempt in range(4):
            try:
                url='https://api.censusreporter.org/1.0/data/show/acs2024_5yr?'+urlencode(params,safe=',')
                payload=json.loads(subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--max-time','180',url]))
                if payload.get('release',{}).get('id')!='acs2024_5yr':raise ValueError('Wrong ACS release')
                path.write_text(json.dumps(payload));break
            except Exception:
                if attempt==3:raise
                time.sleep(2*(attempt+1))
    p=json.loads(path.read_text())
    assert p['release']['id']=='acs2024_5yr'
    return county,geo,p

codes=sorted({c for g in groups.values() for c in g.get('codes',g.get('subtract',[]))})
tables=sorted({c.split('_')[0] for c in codes})
jobs=[]
for geo in ['150','140']:
    ts=[t for t in tables if geo=='140' or t not in ['B18101','B05002','B05005']]
    for county in COUNTIES:
        for i in range(0,len(ts),8):jobs.append((county,geo,ts[i:i+8]))
print(f'Downloading {len(tables)} ACS tables for both geographies',flush=True)
records={'150':{},'140':{}}; metadata={}
with ThreadPoolExecutor(max_workers=4) as pool:
    for county,geo,p in pool.map(fetch,jobs):
        metadata.update(p['tables'])
        for gid,values in p['data'].items():
            if not gid.startswith(geo+'00US'):continue
            r=records[geo].setdefault(gid.split('US')[1],{'geoid':gid.split('US')[1],'name':p['geography'][gid]['name'],'county':COUNTIES[county],'county_fips':'48'+county})
            for table,data in values.items():
                for c,v in data['estimate'].items():r[c+'E']=v if v is not None and v>=0 else np.nan
                for c,v in data['error'].items():r[c+'M']=v if v is not None and v>=0 else np.nan

dictionary=[]
for k,g in groups.items():
    cs=g.get('codes',g.get('subtract'))
    for c in cs:
        table=c.split('_')[0]; assert c.replace('_','') in metadata[table]['columns'],c
    dictionary.append({'variable':k,'label':g['label'],'unit':g['unit'],'denominator':g['denominator'],
       'source_variables':(' - ' if 'subtract' in g else ' + ').join(cs),
       'source_geography':'tract only' if g.get('geography')=='tract' else 'block group and tract',
       'notes':g['note'],'source_url':'https://data.census.gov/table/ACSDT5Y2024.'+cs[0].split('_')[0]})

def prepare(geo):
    raw=pd.DataFrame(records[geo].values()).sort_values('geoid').reset_index(drop=True)
    result=raw[['geoid','name','county','county_fips']].copy()
    kind='block_group' if geo=='150' else 'tract'
    result['tract_geoid']=result.geoid.str[:11]
    result['acs_period']='2020-2024'; result['estimate_type']='ACS 5-year estimate'
    result=result.merge(pd.read_csv(RAW/f'{kind}_locations.csv',dtype={'geoid':str}),on='geoid',validate='1:1')
    assert len(result)==len(raw)
    for k,g in groups.items():
        cs=g.get('codes',g.get('subtract')); es=[c.replace('_','')+'E' for c in cs];ms=[c.replace('_','')+'M' for c in cs]
        if geo=='150' and g.get('geography')=='tract':
            result[k]=np.nan;result[k+'_moe']=np.nan;continue
        assert all(c in raw for c in es),es
        result[k]=raw[es].sum(axis=1,min_count=len(es)) if 'subtract' not in g else raw[es[0]]-raw[es[1]]
        result[k+'_moe']=np.sqrt(raw[ms].pow(2).sum(axis=1,min_count=len(ms)))
    return result
bg=prepare('150');tract=prepare('140')
cross=pd.read_csv(PROC/'block_group_h8_crosswalk.csv',dtype={'bg_geoid':str,'tract_geoid':str,'h3_id':str})
assert set(bg.geoid)==set(cross.bg_geoid)
assert np.allclose(cross.groupby('bg_geoid').pop_weight.sum(),1)
tcross=cross.groupby(['tract_geoid','h3_id'],as_index=False).block_population.sum()
tcross['weight']=tcross.groupby('tract_geoid').block_population.transform(lambda s:s/s.sum() if s.sum()>0 else np.repeat(1/len(s),len(s)))
h3=pd.read_csv(RAW/'h3_locations.csv',dtype={'h3_id':str})
assert not h3.h3_id.duplicated().any()
h3['acs_period']='2020-2024';h3['estimate_type']='ACS counts allocated using 2020 block population'
h3['allocation_status']=np.where(h3.h3_id.isin(cross.h3_id),'matched crosswalk','no source-block representative point')
county_links=cross.assign(county=cross.bg_geoid.str[:5].str[2:].map(COUNTIES)).groupby('h3_id').county.agg(lambda s:'; '.join(sorted(set(s))))
h3['source_counties']=h3.h3_id.map(county_links)
h3['source_block_groups']=h3.h3_id.map(cross.groupby('h3_id').bg_geoid.nunique()).fillna(0).astype(int)
checks=[]
for k,g in groups.items():
    if g.get('geography')=='tract':
        a=tcross.merge(tract[['geoid',k]],left_on='tract_geoid',right_on='geoid',validate='m:1');w=a.weight;source=tract
    else:
        a=cross.merge(bg[['geoid',k]],left_on='bg_geoid',right_on='geoid',validate='m:1');w=a.pop_weight;source=bg
    a['allocated']=a[k]*w
    sums=a.groupby('h3_id').allocated.agg(lambda s:s.sum() if s.notna().all() else np.nan)
    h3[k]=h3.h3_id.map(sums)
    delta=h3[k].sum()-source[k].sum()
    assert abs(delta)<1e-5,(k,delta)
    checks.append({'variable':k,'source_geography':'tract' if source is tract else 'block group','source_total':source[k].sum(),'h3_allocated_total':h3[k].sum(),'difference':delta,'block_group_total':bg[k].sum(min_count=1),'tract_total':tract[k].sum(min_count=1)})

def shares(df):
    result=df.copy()
    for k,g in groups.items():
        den=g['denominator']
        if den!=k:
            result[k+'_pct']=100*result[k]/result[den].where(result[den]>0)
            v=result[k+'_pct'].dropna()
            assert ((v>=-1e-8)&(v<=100+1e-8)).all(),k
    return result
files={}
for name,df in [('block_groups',bg),('tracts',tract),('h3_r8',h3)]:
    df=shares(df)
    path=OUT/f'austin_metro_demographics_{name}.csv'
    df.to_csv(path,index=False,float_format='%.8f',na_rep='')
    files[name]={'rows':len(df),'columns':len(df.columns),'csv':path.name}
    # Typed workbook input; XLSX preserves geographic IDs as strings.
    (RAW/f'review_{name}.json').write_text(df.to_json(orient='split',index=False))
pd.DataFrame(dictionary).to_csv(OUT/'variable_dictionary.csv',index=False)
pd.DataFrame(checks).to_csv(OUT/'allocation_checks.csv',index=False)
(RAW/'review_dictionary.json').write_text(json.dumps(dictionary))
(RAW/'review_checks.json').write_text(pd.DataFrame(checks).to_json(orient='records'))
(OUT/'review_manifest.json').write_text(json.dumps({'acs_release':'acs2024_5yr','variables':len(groups),'files':files,'h3_unmatched_cells':int((h3.allocation_status!='matched crosswalk').sum()),'county_names':list(COUNTIES.values())},indent=2))
(OUT/'README.txt').write_text('''AUSTIN METRO DEMOGRAPHIC REVIEW - ACS 2020-2024 FIVE-YEAR ESTIMATES
Bastrop, Caldwell, Hays, Travis, Williamson counties. Three geographic datasets, each in CSV and XLSX.
CSV fields: base variable = count; _pct = percentage on a 0-100 scale; _moe = 90% ACS count margin of error.
MOEs of sums/differences are approximate root-sum-of-squares. Percent MOEs are not calculated.
Block groups and tracts use direct ACS estimates, not sums of smaller-area estimates. Geographic IDs are text.
Disability and immigration variables use tract sources: their block-group columns are blank.
H3 counts are spatially allocated ACS estimates, not Census observations. Fractional counts are intentional.
Existing 2020 Census block representative-point crosswalk allocates counts within source areas to H3 cells.
Weights are normalized within matched source areas; full source counts are retained, including at grid edges.
Household and family counts also use block population weights as a proxy, not occupied-household weights.
H3 cells without a matched block representative point remain blank, not zero. A matched zero-weight cell can have zero.
H3 percentages are reconstructed from allocated numerator and denominator counts. No medians are allocated.
H3 MOEs are omitted because source ACS MOEs do not measure additional spatial-allocation uncertainty.
2020 block spatial patterns may differ from 2024 development. Use these estimates for review, not household locations.
Direct block-group and tract totals can differ for derived sample-based variables; allocation checks retain both.
Groups overlap and must not be added together. Blank ratios indicate zero/missing denominator, not zero prevalence.
No ACS equivalent is asserted for refugee status, non-permanent residents, subsidized housing or major repair need.
Crowding is not Canadian housing suitability. Noncitizenship is not legal immigration or refugee status.
Single-parent measure means no spouse present; it does not rule out an unmarried partner in the household.
Foreign-born entry measure uses 2010 or later, not the Metrolinx 2016-2021 interval.
Source: US Census Bureau ACS 2024 five-year tables, retrieved via Census Reporter API with release pinned.
https://api.censusreporter.org/1.0/data/show/acs2024_5yr
https://www.census.gov/programs-surveys/acs
2020 block source: https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/Texas/
These review files do not update the public dashboard or select its final ten groups.
''')
print(json.dumps({'files':files,'variables':len(groups),'unmatched_h3':int((h3.allocation_status!='matched crosswalk').sum())},indent=2),flush=True)
