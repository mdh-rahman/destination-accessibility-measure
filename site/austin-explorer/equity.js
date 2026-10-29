/* Embedded equity review shares the dashboard's selectors and population definitions. */
let requestedEquity=new URLSearchParams(location.search).get('view')==='equity';
let equityOpen=false,equityReady=false;
window.equityViewActive=()=>equityOpen;
function syncEquity(){
 if(requestedEquity&&!equityOpen){requestedEquity=false;$('equityViewButton').click();return;}
 if(!equityOpen)return;
 const unsupported=state.mode==='comparison'||(state.scenario==='essential_destinations'&&state.series==='mean_nearest__8');
 $('equityMessage').hidden=!unsupported;$('equityFrame').hidden=unsupported;
 if(unsupported){$('equityMessage').textContent=state.mode==='comparison'?'Choose Auto or Transit + walk to inspect the population-weighted distributions for that mode.':'The eight-category average is unavailable for incomplete baskets. To compare all populations without dropping these origins, choose “Destination types within 15, 30 or 60 minutes.” Click an origin in Map to inspect the eight component times and the number of categories reached.';return;}
 if(equityReady)$('equityFrame').contentWindow.postMessage({type:'dam-equity-selection',scenario:state.scenario,mode:state.mode,series:state.series,region:state.region,group:state.populationGroup},location.origin);
}
window.syncEquity=syncEquity;
$('equityViewButton').onclick=()=>{
 equityOpen=true;document.querySelector('.map-panel').classList.add('equity-active');$('equityPanel').hidden=false;$('equityViewButton').classList.add('active');$('mapViewButton').classList.remove('active');
 if(state.populationGroup==='total_population'){$('populationGroup').value='below_200_poverty';state.populationGroup='below_200_poverty';render();updateURL();}
 if(!$('equityFrame').getAttribute('src'))$('equityFrame').src='population-review/review.html?embedded=1';
 syncEquity();updateURL();
};
$('mapViewButton').onclick=()=>{equityOpen=false;document.querySelector('.map-panel').classList.remove('equity-active');$('equityPanel').hidden=true;$('equityViewButton').classList.remove('active');$('mapViewButton').classList.add('active');map.invalidateSize();updateURL();};
window.addEventListener('message',e=>{if(e.origin===location.origin&&e.source===$('equityFrame').contentWindow&&e.data?.type==='dam-equity-ready'){equityReady=true;syncEquity();}});
