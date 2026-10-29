/* Linked, descriptive equity charts. No routing or demographic estimation occurs here. */
let insightBasis="share",insightSelected=null,insightPoints=[],prioritySet=new Set(),insightSummary=null;
fetch('data/population/equity-summaries.json').then(r=>r.json()).then(d=>{insightSummary=d;if(state.result)renderMapInsights();}).catch(()=>{$('insightNotes').textContent='Benchmark data could not be loaded.';});
function weightedPercentile(items,p){let a=items.filter(x=>x.w>0&&!Number.isNaN(x.v)).sort((a,b)=>a.v-b.v),sum=a.reduce((s,x)=>s+x.w,0),acc=0;if(!sum)return null;for(const x of a){acc+=x.w;if(acc>=sum*p)return x.v;}return null;}
function canvasChart(id){let el=$(id),w=el.clientWidth||320,h=250;el.width=w*2;el.height=h*2;const c=el.getContext('2d');c.scale(2,2);c.clearRect(0,0,w,h);c.font='11px system-ui';return{c,w,h,l:45,r:w-14,t:22,b:205};}
function chartAxes(a,xmax,ymax,xlabel,ylabel){const {c,l,r,t,b,w}=a;c.fillStyle='#526875';c.strokeStyle='#e3e8eb';c.lineWidth=1;for(let j=0;j<=4;j++){let y=b-(b-t)*j/4;c.beginPath();c.moveTo(l,y);c.lineTo(r,y);c.stroke();c.textAlign='right';c.fillText((ymax*j/4).toLocaleString('en-US',{notation:'compact',maximumFractionDigits:1}),l-5,y+4);c.textAlign='center';c.fillText((xmax*j/4).toLocaleString('en-US',{notation:'compact',maximumFractionDigits:1}),l+(r-l)*j/4,b+17);}c.fillText(xlabel,w/2,242);c.textAlign='left';c.fillText(ylabel,l,12);}
function renderMapInsights(){
 if(!state.result||!populationData)return;renderSelectedOrigin();const ser=currentSeries(),special=state.mode==='comparison'||(state.scenario==='essential_destinations'&&state.series==='mean_nearest__8');
 $('insightContent').hidden=special;$('insightUnavailable').hidden=!special;
 if(special){$('insightUnavailable').textContent=state.mode==='comparison'?'Choose Auto or Transit + walk for population comparisons.':'For a comparison that retains incomplete baskets, choose destination types reachable within a time limit. The average is unavailable wherever any of the eight categories is unreachable.';prioritySet.clear();paintPriority();$('priorityNote').textContent='Priority highlighting is unavailable for this measure. Choose a single mode and a supported destination measure.';return;}
 const group=selectedPopulation(),reference=group?.denominator||'total_population',time=ser.unit==='minutes',cap=state.mode==='drive'?60:90,area=state.region==='austin'?'City of Austin':'Austin metro';
 const indices=state.grid.features.map((f,i)=>state.region==='metro'||f.properties.region==='austin'?i:-1).filter(i=>i>=0);
 if(insightSelected!=null&&!indices.includes(insightSelected))insightSelected=null;
 const count=insightBasis==='count',xvalue=i=>count?populationValue(i,state.populationGroup):(()=>{let n=populationValue(i,state.populationGroup),den=populationValue(i,reference);return Number.isFinite(n)&&den>0?100*n/den:null;})();
 const eligible=indices.filter(i=>populationValue(i,reference)>0&&Number.isFinite(xvalue(i))),xs=eligible.map(xvalue).sort((a,b)=>a-b),demoCut=quantile(xs,.75);
 const summary=insightSummary?.[`${state.scenario}__${state.mode}__${state.series}`]?.regions[state.region],threshold=summary?.threshold;
 const low=i=>time?(ser.values[i]==null||(threshold!=null&&ser.values[i]>=threshold)):(ser.values[i]!=null&&threshold!=null&&ser.values[i]<=threshold);
 prioritySet=new Set($('priorityAreas').value==='off'||state.populationGroup==='total_population'||!summary?[]:eligible.filter(i=>xvalue(i)>0&&xvalue(i)>=demoCut&&low(i)));
 paintPriority();
 $('insightHeading').textContent=area;$('scatterDescription').textContent=`${selectedPopulationLabel()} · each dot is an H3 cell; bubble area shows total population.`;
 $('priorityNote').textContent=$('priorityAreas').value==='off'?'Priority outlines are off.':state.populationGroup==='total_population'?'Select a specific population group to highlight priority areas.':`${prioritySet.size.toLocaleString()} cells outlined: low access plus group ${count?'count':'share'} ≥ ${demoCut==null?'—':demoCut.toLocaleString('en-US',{maximumFractionDigits:1})}${count?'':'%'}. Low-access cutoff: ${threshold==null?'no modeled route within '+cap+' minutes':fmt(threshold,ser.unit)+(ser.unit==='jobs'?' jobs':'')}${time?' or longer':' or less'}. Demographic cutoff: upper quartile of cells with a known, positive reference population in this study area. Ties included.`;
 const a=canvasChart('accessScatter'),finite=eligible.filter(i=>Number.isFinite(ser.values[i])),xmax=Math.max(count?1:100,...xs),ymax=Math.max(1,...finite.map(i=>ser.values[i])),xx=v=>a.l+(a.r-a.l)*v/xmax,yy=v=>a.b-(a.b-a.t)*v/ymax;
 chartAxes(a,xmax,ymax,count?'Selected group count':'Selected group share (%)',time?'Travel time (minutes)':ser.unit==='types'?'Destination types reachable':`Reachable ${ser.unit}`);
 const c=a.c;
 if(prioritySet.size&&threshold!=null){c.fillStyle='rgba(190,87,61,.12)';let top=time?yy(ymax):yy(threshold),bottom=time?yy(threshold):yy(0);c.fillRect(xx(demoCut),top,a.r-xx(demoCut),bottom-top);}
 const maxPop=Math.max(1,...finite.map(i=>populationValue(i,'total_population')||0));insightPoints=[];
 for(const i of [...finite].sort((a,b)=>(a===insightSelected)-(b===insightSelected))){let x=xx(xvalue(i)),y=yy(ser.values[i]),radius=Math.max(1.5,8*Math.sqrt((populationValue(i,'total_population')||0)/maxPop));c.beginPath();c.arc(x,y,radius,0,Math.PI*2);c.fillStyle=i===insightSelected?'#e3a024':prioritySet.has(i)?'#be573d':'rgba(17,125,120,.45)';c.fill();insightPoints.push({i,x,y,radius});}
 let trend='';if(finite.length>=3){let xm=finite.reduce((s,i)=>s+xvalue(i),0)/finite.length,ym=finite.reduce((s,i)=>s+ser.values[i],0)/finite.length,sxx=0,syy=0,sxy=0;for(const i of finite){let x=xvalue(i)-xm,y=ser.values[i]-ym;sxx+=x*x;syy+=y*y;sxy+=x*y;}if(sxx>0&&syy>0){let slope=sxy/sxx,intercept=ym-slope*xm;c.save();c.beginPath();c.rect(a.l,a.t,a.r-a.l,a.b-a.t);c.clip();c.strokeStyle='#dba12b';c.lineWidth=2;c.beginPath();c.moveTo(xx(0),yy(intercept));c.lineTo(xx(xmax),yy(intercept+slope*xmax));c.stroke();c.restore();trend=`Unweighted cell-level trend: R² ${(sxy*sxy/(sxx*syy)).toFixed(2)}. `;}}
 const noRoute=eligible.filter(i=>ser.values[i]==null).length;
 $('scatterNotes').textContent=`${trend}${finite.length.toLocaleString()} cells plotted; ${noRoute.toLocaleString()} ${time?'without a modeled route':'with unavailable values'} omitted from scatter and trend. Association is descriptive, not causal. Click a dot or map cell to link the charts.`;
 const binCount=10,upper=Math.max(1,...indices.map(i=>ser.values[i]||0)),bins=time?binCount:ser.unit==='types'?9:binCount;
 function distribution(field){let weights=indices.map(i=>({i,w:populationValue(i,field),v:ser.values[i]==null?Infinity:ser.values[i]})).filter(x=>x.w>0);let total=weights.reduce((s,x)=>s+x.w,0),hist=Array(bins).fill(0),missing=0;for(const x of weights){if(!Number.isFinite(x.v)){missing+=x.w;continue;}let b=ser.unit==='types'?Math.round(x.v):Math.min(bins-1,Math.floor(x.v/upper*bins));hist[b]+=x.w;}return{hist:hist.map(x=>total?100*x/total:0),median:weightedPercentile(weights,.5),missing:total?100*missing/total:0};}
 const selected=distribution(state.populationGroup),ref=distribution(reference),d=canvasChart('accessDistribution'),maxY=Math.max(10,...selected.hist,...ref.hist),dx=v=>d.l+(d.r-d.l)*v/upper,dy=v=>d.b-(d.b-d.t)*v/maxY;
 chartAxes(d,upper,maxY,time?'Travel time (minutes)':ser.unit==='types'?'Destination types reachable':`Reachable ${ser.unit}`,'Share of group (%)');
 for(const [st,color] of [[ref,'#7a858d'],[selected,'#117d78']]){d.c.strokeStyle=color;d.c.lineWidth=2;d.c.beginPath();st.hist.forEach((v,j)=>{let x=ser.unit==='types'?j:(j+.5)*upper/bins;if(j)d.c.lineTo(dx(x),dy(v));else d.c.moveTo(dx(x),dy(v));});d.c.stroke();if(Number.isFinite(st.median)){d.c.setLineDash(color==='#7a858d'?[4,3]:[]);d.c.beginPath();d.c.moveTo(dx(st.median),d.t);d.c.lineTo(dx(st.median),d.b);d.c.stroke();d.c.setLineDash([]);}}
 if(insightSelected!=null&&Number.isFinite(ser.values[insightSelected])){d.c.strokeStyle='#e3a024';d.c.lineWidth=3;d.c.beginPath();d.c.moveTo(dx(ser.values[insightSelected]),d.t);d.c.lineTo(dx(ser.values[insightSelected]),d.b);d.c.stroke();}
 const medianText=v=>v==null?'unavailable':Number.isFinite(v)?fmt(v,ser.unit):time?`beyond ${cap} minutes`:'unavailable';
 $('distributionNotes').textContent=`Group median: ${medianText(selected.median)}. Reference median: ${medianText(ref.median)}. ${time?'Not reached within the routing limit':'Unavailable'}: ${selected.missing.toFixed(1)}% of group, ${ref.missing.toFixed(1)}% of reference. Reference: ${reference.replaceAll('_',' ')}. Both distributions use their own totals, including unreached origins. Medians are population-weighted.`;
 $('insightNotes').textContent='Priority areas are a screening tool, not official designations. Low access uses the selected area’s resident-weighted 75th percentile of travel time or 25th percentile of supply. Unreached travel times remain censored. Census counts allocated to H3 cells are estimates; household and family locations use population as a proxy.';
}
function paintPriority(){if(!gridLayer)return;gridLayer.eachLayer(l=>{const i=l.feature._i,inArea=state.region==='metro'||l.feature.properties.region==='austin';l.setStyle({color:i===insightSelected?'#e3a024':prioritySet.has(i)?'#be573d':'#fff',weight:i===insightSelected?3:prioritySet.has(i)?2:.25,opacity:inArea?1:0});});}
function renderSelectedOrigin(){
 if(insightSelected!=null&&state.region==='austin'&&state.grid.features[insightSelected].properties.region!=='austin')insightSelected=null;
 const box=$('selectedOrigin');
 if(insightSelected==null){box.textContent='Select a map cell or scatter point to inspect its access and population.';return;}
 const i=insightSelected,ser=currentSeries(),id=state.grid.features[i].properties.h3_id;
 box.innerHTML=`<strong>Selected H3 cell</strong><small>${id}</small><p>${ser.label}: <strong>${fmt(ser.values[i],ser.unit)}</strong></p>${populationPopupForCell(i)}${basketPopup(i)}`;
}
function selectInsight(i){
 if(state.region==='austin'&&state.grid.features[i].properties.region!=='austin')return;
 insightSelected=i;map.closePopup();
 document.querySelector('.map-panel').classList.remove('insights-closed');$('insightsToggle').setAttribute('aria-expanded','true');map.invalidateSize();renderMapInsights();
}
window.selectInsight=selectInsight;
$('accessScatter').onclick=e=>{const rect=e.target.getBoundingClientRect(),x=e.clientX-rect.left,y=e.clientY-rect.top;let point=insightPoints.map(p=>({...p,d:Math.hypot(p.x-x,p.y-y)})).sort((a,b)=>a.d-b.d)[0];if(point&&point.d<Math.max(12,point.radius)){selectInsight(point.i);}};
$('priorityAreas').onchange=()=>{if($('priorityAreas').value!=='off')insightBasis=$('priorityAreas').value;renderMapInsights();};
$('insightsToggle').onclick=()=>{const panel=document.querySelector('.map-panel');panel.classList.toggle('insights-closed');$('insightsToggle').setAttribute('aria-expanded',String(!panel.classList.contains('insights-closed')));map.invalidateSize();renderMapInsights();};
window.addEventListener('resize',()=>{if(state.result)renderMapInsights();});
if(window.innerWidth<1000){document.querySelector('.map-panel').classList.add('insights-closed');$('insightsToggle').setAttribute('aria-expanded','false');map.invalidateSize();}
window.renderMapInsights=renderMapInsights;
