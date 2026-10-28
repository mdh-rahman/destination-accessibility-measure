/* Public aggregate ACS context and origin-weighted outcomes. */
let populationData, populationLayer, populationEpoch=0;
const populationShapes={};
async function initPopulation(){
 populationData=await fetch('data/population/population.json').then(r=>{if(!r.ok)throw Error('Population data unavailable');return r.json()});
 const groups=populationData.groups;
 const primary=groups.filter(g=>!['people_of_color','total_population','children_household_universe'].includes(g.group_id));
 $('populationGroup').innerHTML='<option value="total_population">All residents</option>'+primary.map(g=>`<option value="${g.group_id}">${g.label}</option>`).join('')+'<optgroup label="Optional combined summary"><option value="people_of_color">People of color</option></optgroup>';
 const q=new URLSearchParams(location.search); const selected=q.get('populationGroup');
 if(groups.some(g=>g.group_id===selected))$('populationGroup').value=selected;
 $('populationMap').checked=q.get('populationMap')==='true';
 $('populationGroup').addEventListener('change',()=>{renderPopulation();updateURL()});
 $('populationMap').addEventListener('change',()=>{render();updateURL()});
}
async function renderPopulation(){
 if(!populationData)return;
 const epoch=++populationEpoch;
 const group=populationData.groups.find(g=>g.group_id===$('populationGroup').value);
 state.populationGroup=group.group_id;state.populationMap=$('populationMap').checked;
 const ser=currentSeries(); if(!ser)return;
 const [field,param]=state.series.split('__');
 const rows=populationData.outcomes.filter(x=>x.scenario===state.scenario&&x.region===state.region&&x.opportunity_field===field&&Number(x.parameter_value)===Number(param)&&x.group_id===group.group_id);
 const modes=state.mode==='comparison'?['drive','walk_transit']:[state.mode];
 const time=ser.unit==='minutes'||scenario().measure==='time';
 let html='<table><thead><tr><th>Peak outcome</th>'+modes.map(m=>`<th>${m==='drive'?'Auto':'Transit + walk'}</th>`).join('')+'</tr></thead><tbody>';
 const cells=(label,fn)=>'<tr><th>'+label+'</th>'+modes.map(m=>{const row=rows.find(r=>r.mode===m);return '<td>'+(row?fn(row):'Unavailable')+'</td>'}).join('')+'</tr>';
 const unit=field==='acreage'?'acres':field==='park_count'?'parks':time?'minutes':'jobs';
 html+=cells(time?'Mean time (capped)':'Mean accessible supply',r=>fmt(r.mean_access,unit));
 html+=cells(time?'Reached required destinations':'Reached ≥1 opportunity',r=>r.reachable_share==null?'—':`${(r.reachable_share*100).toFixed(1)}%`);
 html+=cells(group.unit==='household'?'All-household mean':'All-resident mean',r=>fmt(r.reference_mean,unit));
 html+='</tbody></table>';
 if(time)html+='<p class="population-note">Unreached destinations are assigned the 60-minute auto or 90-minute transit limit in this capped mean. This is not their actual travel time; check reachability alongside it.</p>';
 if(!time)html+='<p class="population-note">Means include origins with zero opportunities. These group-weighted means differ from the unweighted map statistics above.</p>';
 $('populationOutcome').innerHTML=html;
 $('populationSource').textContent=`ACS 2024 five-year estimates · ${group.source_geography==='tract'?'census tracts':'census block groups'} · ${group.unit==='household'?'household':'resident'} weights`;
 if(populationLayer){map.removeLayer(populationLayer);populationLayer=null;}
 gridLayer.eachLayer(l=>{const inRegion=state.region==='metro'||l.feature.properties.region==='austin';if(state.populationMap)l.setStyle({fillOpacity:0,opacity:0});});
 if(!state.populationMap)return;
 if(group.group_id==='total_population'){
   $('populationSource').textContent+=' · Select a specific group to map its share.';
   $('populationMap').checked=false;state.populationMap=false;render();return;
 }
 const geo=group.source_geography;
 try{
  if(!populationShapes[geo])populationShapes[geo]=await fetch(`data/population/${geo}.geojson`).then(r=>{if(!r.ok)throw Error('Map unavailable');return r.json()});
  if(epoch!==populationEpoch)return;
  const shades=['#f1eef6','#bdc9e1','#74a9cf','#2b8cbe','#045a8d'];
  const share=p=>p[group.denominator]>0?p[group.group_id]/p[group.denominator]:null;
  populationLayer=L.geoJSON(populationShapes[geo],{style:f=>{const v=share(f.properties);return{fillColor:v==null?'#ccc':shades[Math.min(4,Math.floor(v*5))],fillOpacity:.72,color:'#fff',weight:.5}},onEachFeature:(f,l)=>{const p=f.properties,v=share(p),moe=p[group.group_id+'_moe'];l.bindPopup(`<strong>${group.label}</strong><p>${v==null?'Not available':(v*100).toFixed(1)+'%'} · ${Math.round(p[group.group_id]||0).toLocaleString()} ${group.unit==='household'?'households':'residents'}</p><small>${geo==='tract'?'Tract':'Block group'} ${p.GEOID||''}${moe!=null?'<br>Count margin of error: ±'+Math.round(moe).toLocaleString():''}<br>ACS 2024 five-year estimate</small>`);}}).addTo(map);
  if(overlays.cityBoundary)overlays.cityBoundary.bringToFront();
  $('mapTitle').textContent=group.label;
  $('mapKicker').textContent='DEMOGRAPHIC CONTEXT · ACS 2024';
  $('legend').innerHTML='<h3>Share of relevant population</h3>'+shades.map((c,i)=>`<div class="legend-row"><i class="swatch" style="background:${c}"></i><span>${i*20}–${(i+1)*20}%</span></div>`).join('')+'<div class="legend-row"><i class="swatch" style="background:#ccc"></i><span>No denominator</span></div>';
  $('populationSource').textContent+=' · Full census areas are shown; the Austin outline is a reference, not a clipped demographic estimate.';
 }catch(e){showStatus('Demographic map unavailable');console.error(e)}
}
