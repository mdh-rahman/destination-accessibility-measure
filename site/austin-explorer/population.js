/* Public aggregate ACS context and origin-weighted outcomes. */
let populationData;

async function initPopulation(){
  populationData=await fetch('data/population/population.json').then(r=>{
    if(!r.ok)throw Error('Population data unavailable');
    return r.json();
  });
  const groups=populationData.groups;
  const primary=groups.filter(g=>g.group_id!=='total_population');
  $('populationGroup').innerHTML='<option value="total_population">All residents</option>'+primary.map(g=>`<option value="${g.group_id}">${g.label}</option>`).join('');
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

function populationPopupForCell(index){
  const group=selectedPopulation(),share=populationShare(index);
  if(!group||share==null)return'';
  const count=populationValue(index,state.populationGroup);
  return`<span class="population-popup">${group.label}: ${(share*100).toFixed(1)}% · ${Math.round(count||0).toLocaleString()} estimated ${({household:'households',family:'families',worker:'workers',person:'residents'}[group.unit]||'people')}</span>`;
}
