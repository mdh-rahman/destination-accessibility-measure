/* Public aggregate ACS context and origin-weighted outcomes. */
let populationData;

async function initPopulation(){
  populationData=await fetch('data/population/population.json').then(r=>{
    if(!r.ok)throw Error('Population data unavailable');
    return r.json();
  });
  const groups=populationData.groups;
  const primary=groups.filter(g=>!['people_of_color','total_population','children_household_universe'].includes(g.group_id));
  $('populationGroup').innerHTML='<option value="total_population">All residents</option>'+primary.map(g=>`<option value="${g.group_id}">${g.label}</option>`).join('')+'<optgroup label="Optional combined summary"><option value="people_of_color">People of color</option></optgroup>';
  const selected=new URLSearchParams(location.search).get('populationGroup');
  if(groups.some(g=>g.group_id===selected))$('populationGroup').value=selected;
  state.populationGroup=$('populationGroup').value;
  $('populationGroup').addEventListener('change',()=>{
    state.populationGroup=$('populationGroup').value;
    render();
    updateURL();
  });
}

function selectedPopulation(){
  return populationData?.groups.find(g=>g.group_id===state.populationGroup);
}

function selectedPopulationLabel(){
  return state.populationGroup==='total_population'?'All residents':selectedPopulation()?.label||'Selected group';
}

function populationValue(index,field){
  return populationData?.h3?.[field]?.[index]??null;
}

function populationShare(index){
  const group=selectedPopulation();
  if(!group||state.populationGroup==='total_population')return null;
  const numerator=populationValue(index,state.populationGroup),denominator=populationValue(index,group.denominator);
  return Number.isFinite(numerator)&&Number.isFinite(denominator)&&denominator>0?numerator/denominator:null;
}

function populationStyleForCell(index,baseOpacity){
  const share=populationShare(index);
  if(share==null)return{fillOpacity:baseOpacity,opacity:1};
  const emphasis=.18+.72*Math.sqrt(Math.max(0,Math.min(1,share)));
  return{fillOpacity:baseOpacity*emphasis,opacity:.25+.75*emphasis};
}

function populationPopupForCell(index){
  const group=selectedPopulation(),share=populationShare(index);
  if(!group||share==null)return'';
  const count=populationValue(index,state.populationGroup);
  return`<span class="population-popup">${group.label}: ${(share*100).toFixed(1)}% · ${Math.round(count||0).toLocaleString()} estimated ${group.unit==='household'?'households':'residents'}</span>`;
}

function outcomeRows(group,field,param){
  return populationData.outcomes.filter(x=>x.scenario===state.scenario&&x.region===state.region&&x.opportunity_field===field&&Number(x.parameter_value)===Number(param)&&x.group_id===group.group_id);
}

function renderPopulation(){
  if(!populationData||!currentSeries())return;
  const group=selectedPopulation();
  const [field,param]=state.series.split('__');
  const rows=outcomeRows(group,field,param);
  const modes=state.mode==='comparison'?['drive','walk_transit']:[state.mode];
  const time=currentSeries().unit==='minutes'||scenario().measure==='time';
  const unit=field==='acreage'?'acres':time?'minutes':'jobs';
  const modeName=m=>m==='drive'?'Auto':'Transit + walk';
  let html='<table><thead><tr><th>Average access</th>'+modes.map(m=>`<th>${modeName(m)}</th>`).join('')+'</tr></thead><tbody>';
  html+='<tr><th>'+selectedPopulationLabel()+'</th>'+modes.map(m=>{const row=rows.find(r=>r.mode===m);return`<td>${row?fmt(row.mean_access,unit):'Unavailable'}</td>`}).join('')+'</tr>';
  html+='<tr><th>'+((group?.unit==='household')?'All households':'All residents')+'</th>'+modes.map(m=>{const row=rows.find(r=>r.mode===m);return`<td>${row?fmt(row.reference_mean,unit):'Unavailable'}</td>`}).join('')+'</tr></tbody></table>';
  $('populationOutcome').innerHTML=html;
  if(state.populationGroup==='total_population'){
    $('populationSource').textContent='Select a population group to emphasize where that group lives and compare its average access.';
  }else{
    $('populationSource').textContent=`Map color = accessibility · opacity = local ${group.label.toLowerCase()} share · ACS 2024 five-year estimated ${group.unit}s`;
  }
}
