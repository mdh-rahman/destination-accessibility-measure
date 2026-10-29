#!/usr/bin/env python3
"""Offline population-weighted review; no routing rerun or website mutation.
Run: python build_equity_review.py --root PATH [--output PATH]
Requires pandas/numpy. Template must be alongside this script.
"""
import argparse, json, hashlib
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

GROUPS = [
 ('renter_households','Renter households','households','total_households','All households'),
 ('commute_60_plus','Commuters: 60+ minutes','workers','commuting_workers','Workers commuting to work'),
 ('below_200_poverty','Below 200% of poverty','people','below_200_poverty_universe','People with poverty status'),
 ('no_vehicle_households','No-vehicle households','households','vehicle_household_universe','Households with vehicle data'),
 ('families_with_own_children','Families with children','families','total_families','All families'),
 ('adults_65_plus','Adults 65+','people','total_population','All residents'),
 ('people_with_disability','People with disabilities','people','disability_universe','Civilian noninstitutionalized population'),
 ('limited_english_households','Limited-English households','households','language_household_universe','Households with language data'),
 ('single_parent_families','Single-parent families','families','families_with_own_children','Families with own children under 18'),
 ('housing_cost_30_plus','Housing-cost-burdened households','households','housing_cost_known','Households with computable housing costs'),
 ('hispanic_latino','Hispanic / Latino','people','race_ethnicity_universe','All residents with race/ethnicity data'),
 ('black_nh','Non-Hispanic Black','people','race_ethnicity_universe','All residents with race/ethnicity data')]
LABELS={'childcare_nearest':'Nearest childcare facility','essential_destinations':'Essential destination types reachable','grocery_nearest':'Nearest grocery store','urgent_care_nearest':'Nearest urgent care','hospital_nearest':'Nearest hospital','park_nearest':'Nearest park','childcare_fifth_nearest':'Fifth childcare facility','grocery_third_nearest':'Third grocery store','hospital_second_nearest':'Second hospital','library_nearest':'Nearest library','pharmacy_nearest':'Nearest pharmacy','public_center_nearest':'Nearest public center','urgent_care_third_nearest':'Third urgent care','jobs_cumulative':'Jobs reachable','park_reachable_supply':'Park acreage reachable'}

def quantile(x,w,p):
    ok=(w>0)&np.isfinite(w)&~np.isnan(x)
    if not ok.any(): return np.nan
    x,w=x[ok],w[ok]; ix=np.argsort(x,kind='stable'); x,w=x[ix],w[ix]
    return x[min(np.searchsorted(np.cumsum(w),w.sum()*p),len(x)-1)]

def clean(v):
    if isinstance(v,dict): return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [clean(x) for x in v]
    if isinstance(v,np.ndarray): return clean(v.tolist())
    if isinstance(v,(np.floating,float)): return round(float(v),6) if np.isfinite(v) else None
    if isinstance(v,np.integer): return int(v)
    return v

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--output',type=Path)
    args=ap.parse_args(); root=args.root; out=args.output or root/'population-access/output/equity-review'; out.mkdir(parents=True,exist_ok=True)
    poppath=root/'population-access/output/demographic-review/austin_metro_demographics_h3_r8.csv'
    pop=pd.read_csv(poppath).set_index('h3_id'); assert pop.index.is_unique
    selected=pd.read_csv(root/'population-access/output/selected-demographics/austin_metro_selected_demographics_h3_r8.csv').set_index('h3_id')
    for g,*_ in GROUPS:
        if g in selected: assert np.allclose(pop[g],selected[g].reindex(pop.index),equal_nan=True)
    # All-family denominator, allocated with the identical normalized block-population crosswalk.
    family_records={}; family_sources=[]
    for source in sorted((root/'case-studies/austin/data/raw/population_access/review_expanded').glob('acs2024_150_*.json')):
        payload=json.loads(source.read_text())
        if 'B11003' not in payload.get('tables',{}): continue
        assert payload['release']['id']=='acs2024_5yr'
        family_sources.append(source)
        for gid, record in payload['data'].items():
            if gid.startswith('15000US'):
                family_records[gid.split('US')[1]]=record['B11003']['estimate']['B11003001']
    crosspath=root/'case-studies/austin/data/processed/population_access/block_group_h8_crosswalk.csv'
    cross=pd.read_csv(crosspath,dtype={'bg_geoid':str,'h3_id':str})
    assert set(cross.bg_geoid)<=set(family_records)
    assert np.allclose(cross.groupby('bg_geoid').pop_weight.sum(),1)
    cross['families']=cross.bg_geoid.map(family_records)*cross.pop_weight
    pop['total_families']=cross.groupby('h3_id').families.sum(min_count=1).reindex(pop.index)
    assert (pop.families_with_own_children.dropna() <= pop.total_families.dropna()+.01).all()

    grid=json.loads((root/'site/austin-explorer/data/h8-grid.geojson').read_text())
    ids=[f['properties']['h3_id'] for f in grid['features']]; pop=pop.reindex(ids)
    def rings(geom):
        return geom['coordinates'] if geom['type']=='Polygon' else [r for p in geom['coordinates'] for r in p]
    maps=[[[[round(c[0],5),round(c[1],5)] for c in ring] for ring in rings(f['geometry'])] for f in grid['features']]
    boundaries=json.loads((root/'site/austin-explorer/data/county-boundaries.geojson').read_text())
    county=[rings(f['geometry']) for f in boundaries['features']]
    city=json.loads((root/'site/austin-explorer/data/austin-full-purpose.geojson').read_text())
    cityrings=[rings(f['geometry']) for f in city['features']]
    areas={'metro':np.ones(len(pop),bool),'austin':pop.region.eq('austin').to_numpy()}
    assert areas['austin'].any(), 'Austin membership missing'
    data={'groups':[dict(zip(['id','label','unit','reference','reference_label'],g)) for g in GROUPS], 'ids':ids,'maps':maps,'county':county,'city':cityrings,'austin':np.flatnonzero(areas['austin']).tolist(),'population':{g:clean(pop[g].to_numpy()) for g in set([x[0] for x in GROUPS]+[x[3] for x in GROUPS]+['total_population'])},'coordinates':clean(pop[['longitude','latitude']].to_numpy()),'series':[]}
    rows=[]; inputs=[poppath,crosspath]+family_sources; qa=[]
    for path in sorted((root/'case-studies/austin/outputs/working').glob('*/ */am_peak/accessibility.csv'.replace(' ',''))):
        scenario,mode=path.parts[-4:-2]
        if scenario not in LABELS or mode not in ['drive','walk_transit']: continue
        inputs.append(path); frame=pd.read_csv(path); manifest=json.loads(path.with_name('run_manifest.json').read_text()); cap=float(manifest['maximum_trip_minutes']); inputs.append(path.with_name('run_manifest.json'))
        if scenario=='jobs_cumulative': frame=frame[frame.parameter_value.isin([15,30] if mode=='drive' else [30,60])]
        if scenario=='park_reachable_supply': frame=frame[frame.opportunity_field.eq('acreage')]
        for (field,parameter),sub in frame.groupby(['opportunity_field','parameter_value']):
            assert sub.geography_id.is_unique
            sub=sub.set_index('geography_id').reindex(ids); time=sub.measure.dropna().iloc[0]=='kth_nearest_time'
            raw=sub.access_value.to_numpy(float); exists=sub.scenario.notna().to_numpy(); reached=sub.is_reachable.eq(True).to_numpy()
            # Explicit FALSE means no modeled route; absent rows or TRUE with missing values are unknown.
            unreachable=exists & sub.is_reachable.eq(False).to_numpy() if time else np.zeros(len(pop),bool)
            valid=(np.isfinite(raw)&reached)|unreachable if time else np.isfinite(raw)&exists
            values=raw.copy(); values[unreachable]=np.inf; values[~valid]=np.nan
            assert not np.any(values[np.isfinite(values)]<0)
            if time: assert np.all(values[np.isfinite(values)]<=cap+0.001)
            key=f'{scenario}__{mode}__{field}__{parameter}'
            entry={'key':key,'scenario':scenario,'mode':mode,'field':field,'parameter':int(parameter),'title':LABELS[scenario],'time':time,'cap':cap,'values':clean(raw),'valid':np.flatnonzero(valid).tolist(),'unreachable':np.flatnonzero(unreachable).tolist(),'regions':{}}
            xmax=cap if time else max(1.,float(np.nanmax(raw)))
            points=np.unique(np.r_[0,np.linspace(0,xmax,201),np.geomspace(max(.001,xmax/100000),xmax,201)]) if not time else np.linspace(0,cap,181)
            if scenario=='essential_destinations': points=np.arange(9)
            for region,mask in areas.items():
                threshold=quantile(values[mask],pop.total_population.to_numpy(float)[mask],.75 if time else .25)
                low=((values>=threshold) if time else (values<=threshold)) & valid
                area_label='Austin' if region=='austin' else 'Metro'
                policy=area_label+' resident-weighted '+('75th percentile of travel time (ties included)' if time else '25th percentile of supply (ties included)')
                if not np.isfinite(threshold): policy=area_label+': not reached within modeled limit (75th percentile exceeds limit)'
                if not time and threshold==0: policy=area_label+': zero reachable supply (25th percentile is zero)'

                def stats(col):
                    weight=pop[col].to_numpy(float); good=mask & valid & np.isfinite(weight)&(weight>0); total=np.nansum(weight[mask]); included=weight[good].sum()
                    q=[quantile(values[good],weight[good],p) for p in [.25,.5,.75]]
                    whiskers=[quantile(values[good],weight[good],p) for p in [.1,.9]]
                    finite=good&np.isfinite(values)
                    mean=float(np.average(values[finite],weights=weight[finite])) if finite.any() else np.nan
                    wholemean=mean if not np.any(good&unreachable) else np.nan
                    rate=lambda m: float(weight[good&m].sum()/included*100) if included else np.nan
                    curve=[rate(values<=p) for p in points]
                    return {'weight':included,'coverage_pct':included/total*100 if total else np.nan,'q':clean(q),'whiskers':clean(whiskers),'whiskers_censored':[bool(np.isinf(x)) for x in whiskers],'q_censored':[bool(np.isinf(x)) for x in q],'mean':clean(wholemean),'reachable_only_mean':clean(mean) if time else None,'low_pct':rate(low),'no_route_pct':rate(unreachable) if time else None,'zero_pct':rate(values==0) if not time else None,'curve':clean(curve)}
                references={r:stats(r) for r in set(g[3] for g in GROUPS)}
                groups={g:stats(g) for g,*_ in GROUPS}; entry['regions'][region]={'groups':groups,'references':references,'threshold':clean(threshold),'policy':policy,'low':np.flatnonzero(low & mask).tolist()}
                for g,label,unit,reference,ref_label in GROUPS:
                    s=groups[g]; ref=references[reference]
                    row={'series':key,'destination':LABELS[scenario],'mode':mode,'region':region,'opportunity_field':field,'parameter':parameter,'unit':'minutes' if time else ('acres' if scenario=='park_reachable_supply' else 'types' if scenario=='essential_destinations' else 'jobs'),'group':g,'group_label':label,'weight_unit':unit,'reference_label':ref_label,'estimated_group_count':s['weight'],'data_coverage_pct':s['coverage_pct'],'mean':s['mean'],'reachable_only_mean':s['reachable_only_mean'],'low_access_pct':s['low_pct'],'reference_low_access_pct':ref['low_pct'],'low_access_gap_percentage_points':s['low_pct']-ref['low_pct'],'not_reached_within_limit_pct':s['no_route_pct'],'zero_supply_pct':s['zero_pct'],'area_threshold':clean(threshold),'benchmark_region':region,'threshold_rule':policy,'routing_limit_minutes':cap}
                    for j,name in enumerate(['p25','median','p75']):
                        row[name]=s['q'][j]; row[name+'_exceeds_limit']=s['q_censored'][j]; row['reference_'+name]=ref['q'][j]; row['reference_'+name+'_exceeds_limit']=ref['q_censored'][j]
                    for j,name in enumerate(['p10','p90']):
                        row[name]=s['whiskers'][j]; row[name+'_exceeds_limit']=s['whiskers_censored'][j]
                    rows.append(row)
            entry['points']=clean(points); data['series'].append(entry)
            qa.append({'series':key,'cells':len(pop),'valid_cells':int(valid.sum()),'no_route_cells':int(unreachable.sum()),'missing_cells':int((~valid).sum()),'austin_low_access_cells':len(entry['regions']['austin']['low']),'metro_low_access_cells':len(entry['regions']['metro']['low']), 'austin_threshold':entry['regions']['austin']['threshold'],'metro_threshold':entry['regions']['metro']['threshold']})
    assert len(data['series'])>18
    pd.DataFrame(rows).to_csv(out/'group_comparisons.csv',index=False)
    pd.DataFrame(qa).to_csv(out/'quality_checks.csv',index=False)
    payload=json.dumps(clean(data),separators=(',',':'),allow_nan=False)
    template=Path(__file__).with_name('equity_review_template.html').read_text()
    (out/'review.html').write_text(template.replace('__DATA__',payload))
    manifest={'generated_utc':datetime.now(timezone.utc).isoformat(),'series':len(data['series']),'summary_rows':len(rows),'groups':len(GROUPS),'regions':list(areas),'inputs':[{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs]}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (out/'README.txt').write_text('LOCAL REVIEW — not published\nOpen review.html directly in a browser; no server or internet required.\nOutputs: group_comparisons.csv (all group summaries), quality_checks.csv, manifest.json.\nUse selectors for destination, mode, threshold/job type, geography and population. Save chart buttons export SVG; the map exports PNG.\nMethods: counts weight accessibility at H3 origins. Quantiles use the inverse weighted empirical CDF. Non-reached travel times are right-censored, never assigned the limit as an observed value; full means are blank if any weighted origins are censored. Conditional means are explicitly labeled. Missing access is excluded with coverage reported.\nLow access uses the selected-area resident-weighted 75th percentile of travel time or 25th percentile of supply. Threshold ties are included, so the low-access share can exceed 25%. Zero supply thresholds select zero supply; censored time thresholds select all non-reached origins. Austin and metro each use their own distribution; a fixed threshold applies to all groups within the selected area. It is relative disadvantage, not an adequacy standard. Reference weights follow each group denominator.\nACS 2020–2024 five-year estimates allocated using 2020 Census block population crosswalks. Household/family allocation uses population as a proxy. Disability is allocated from tracts. Unmatched population cells remain unknown. Groups overlap. Boxes show weighted 25th–75th percentiles with a median line; whiskers show weighted 10th–90th percentiles. These describe distribution, not confidence intervals. Arrows mark percentiles beyond the routing limit; tails beyond whiskers are not plotted.\nAustin uses existing H3 city membership, not new boundary clipping. Destination availability outside the region is unchanged. Transit represents supplied GTFS/routing coverage, not all regional service or disability-specific routing. Auto for no-vehicle households is hypothetical. Park acres are reachable inventory supply, not per-capita provision, quality or usable acreage.\nReview source models and service calendar before treating these outputs as final. Prior capped summaries and the public website are not modified; this folder supersedes them for this demographic review only.\nLiterature: https://dashboard.transitcenter.org/about ; https://ipea.github.io/aopdata/articles/access_inequality.html ; https://mobilizingjustice.ca/tools-and-guidelines/ ; https://doi.org/10.1007/s11116-023-10460-7\nRebuild: python population-access/scripts/build_equity_review.py --root /path/to/destination-accessibility-measure\n')
    print(json.dumps({'output':str(out),'series':len(data['series']),'rows':len(rows),'html_MB':round((out/'review.html').stat().st_size/1e6,2)}))

if __name__=='__main__': main()
