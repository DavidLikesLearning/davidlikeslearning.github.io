const $ = id => document.getElementById(id);
const SCENARIOS = {
  no_servers: 'No servers', unregulated: 'Servers, unregulated',
  covered_50: 'Servers, 50% covered', covered_100: 'Servers, 100% covered'
};
const METRICS = {
  capacity_gw: {label:'Generation & storage capacity',unit:'GW',digits:1},
  clean_gw: {label:'Clean generation capacity',unit:'GW',digits:1},
  battery_gw: {label:'Battery capacity',unit:'GW',digits:1},
  net_exports_twh: {label:'Net electricity exports',unit:'TWh/yr',digits:1},
  co2_mt: {label:'CO₂ emissions',unit:'Mt/yr',digits:1}
};
const state = {metric:'capacity_gw',year:'2040',scenario:'unregulated',compare:'none',view:'map',region:null};
let records = new Map(), geography = null, regions = [];

function parseCSV(csv) {
  const [header,...lines] = csv.trim().split(/\r?\n/);
  const keys = header.split(',');
  return lines.map(line => Object.fromEntries(line.split(',').map((v,i) => [keys[i],v])));
}
function key(scenario,year,region){return `${scenario}|${year}|${region}`}
function raw(scenario,region){return Number(records.get(key(scenario,state.year,region))?.[state.metric] ?? NaN)}
function value(region){const a=raw(state.scenario,region);return state.compare==='none'?a:a-raw(state.compare,region)}
function format(n,plus=false){return `${plus&&n>0?'+':''}${n.toLocaleString(undefined,{maximumFractionDigits:METRICS[state.metric].digits,minimumFractionDigits:1})}`}
function clamp(x){return Math.min(1,Math.max(0,x))}
function blend(a,b,t){return `rgb(${a.map((v,i)=>Math.round(v+(b[i]-v)*t)).join(',')})`}
function color(v,limit,diverge){
  if(!Number.isFinite(v))return '#d6ddd7';
  if(diverge){const t=clamp(Math.abs(v)/limit);return v<0?blend([247,248,244],[40,102,164],t):blend([247,248,244],[221,167,42],t)}
  return blend([235,242,235],[13,105,94],clamp(v/limit));
}
function ringPath(ring){return ring.map(([lon,lat],i)=>`${i?'L':'M'}${(lon+126)*16.1},${(51-lat)*17.8}`).join('')+'Z'}
function shapePath(geometry){
  const polys=geometry.type==='Polygon'?[geometry.coordinates]:geometry.coordinates;
  return polys.map(poly=>poly.map(ringPath).join('')).join('');
}
function labelPoint(geometry){
  const polys=geometry.type==='Polygon'?[geometry.coordinates]:geometry.coordinates;
  const outer=polys.flatMap(p=>p[0]);let sx=0,sy=0;
  outer.forEach(([lon,lat])=>{sx+=(lon+126)*16.1;sy+=(51-lat)*17.8});
  return [sx/outer.length,sy/outer.length];
}
function selectRegion(region){state.region=region;renderDetail();document.querySelectorAll('.region,.bar-row').forEach(el=>el.classList.toggle('selected',el.dataset.region===region))}
function renderDetail(){
  const r=state.region;if(!r){$('detail-region').textContent='Select a region';$('detail-value').textContent='';return}
  const n=value(r);$('detail-region').textContent=r;
  $('detail-value').innerHTML=`${format(n,state.compare!=='none')} ${METRICS[state.metric].unit}<small>${state.compare==='none'?SCENARIOS[state.scenario]:`${SCENARIOS[state.scenario]} minus ${SCENARIOS[state.compare]}`}</small>`;
}
function renderMap(limit,diverge){
  const svg=$('map');svg.replaceChildren();
  const ns='http://www.w3.org/2000/svg';
  for(const feature of geography.features){
    const region=feature.properties.model_region;if(!regions.includes(region))continue;
    const path=document.createElementNS(ns,'path');path.setAttribute('d',shapePath(feature.geometry));
    path.setAttribute('fill',color(value(region),limit,diverge));path.setAttribute('fill-rule','evenodd');
    path.setAttribute('class','region'+(region===state.region?' selected':''));path.setAttribute('tabindex','0');path.setAttribute('role','button');
    path.setAttribute('aria-label',`${region}: ${format(value(region),state.compare!=='none')} ${METRICS[state.metric].unit}`);
    path.dataset.region=region;path.addEventListener('click',()=>selectRegion(region));
    path.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectRegion(region)}});
    const title=document.createElementNS(ns,'title');title.textContent=`${region}: ${format(value(region),state.compare!=='none')} ${METRICS[state.metric].unit}`;path.append(title);svg.append(path);
  }
  if(state.region){const feature=geography.features.find(f=>f.properties.model_region===state.region);if(feature){
    const [x,y]=labelPoint(feature.geometry);const t=document.createElementNS(ns,'text');t.setAttribute('x',x);t.setAttribute('y',y);t.setAttribute('text-anchor','middle');t.setAttribute('class','region-label');t.textContent=state.region;svg.append(t);
  }}
}
function renderBars(limit,diverge){
  const box=$('bars');box.replaceChildren();
  const ordered=[...regions].sort((a,b)=>value(b)-value(a));
  for(const region of ordered){
    const n=value(region),row=document.createElement('div');row.className='bar-row'+(region===state.region?' selected':'');row.dataset.region=region;
    row.setAttribute('role','button');row.setAttribute('tabindex','0');row.setAttribute('aria-label',`${region}: ${format(n,state.compare!=='none')} ${METRICS[state.metric].unit}`);
    const name=document.createElement('span');name.className='bar-name';name.textContent=region;
    const track=document.createElement('div');track.className='bar-track';const zero=diverge?50:0;track.style.setProperty('--zero',`${zero}%`);
    const fill=document.createElement('div');fill.className='bar-fill';const width=diverge?Math.abs(n)/limit*50:Math.max(0,n)/limit*100;
    fill.style.left=`${diverge&&n<0?50-width:zero}%`;fill.style.width=`${width}%`;fill.style.background=color(n,limit,diverge);track.append(fill);
    const num=document.createElement('span');num.className='bar-number';num.textContent=format(n,state.compare!=='none');row.append(name,track,num);
    row.addEventListener('click',()=>selectRegion(region));row.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectRegion(region)}});box.append(row);
  }
}
function render(){
  if(!geography)return;
  const metric=METRICS[state.metric],compare=state.compare!=='none';
  const vals=regions.map(value),diverge=compare||state.metric==='net_exports_twh';
  const limit=Math.max(...vals.map(v=>diverge?Math.abs(v):v),.001);
  $('chart-kicker').textContent=compare?'Scenario difference':'Regional values';
  $('chart-title').textContent=`${metric.label} · ${state.year}`;
  $('chart-subtitle').textContent=compare?`${SCENARIOS[state.scenario]} minus ${SCENARIOS[state.compare]}`:SCENARIOS[state.scenario];
  if(state.metric==='net_exports_twh'){$('national').hidden=true}else{
    $('national').hidden=false;const total=vals.reduce((a,b)=>a+b,0);
    $('national').innerHTML=`<strong>${format(total,compare)} ${metric.unit}</strong><span>${compare?'Sum of regional differences':'Sum across 26 regions'}</span>`;
  }
  renderMap(limit,diverge);renderBars(limit,diverge);renderDetail();
  $('map-panel').hidden=state.view!=='map';$('bars-panel').hidden=state.view!=='bars';
  $('map-tab').classList.toggle('active',state.view==='map');$('bars-tab').classList.toggle('active',state.view==='bars');
  $('map-tab').setAttribute('aria-pressed',state.view==='map');$('bars-tab').setAttribute('aria-pressed',state.view==='bars');
  $('gradient').style.background=diverge?'linear-gradient(90deg,#2866a4,#f7f8f4 50%,#dda72a)':'linear-gradient(90deg,#ebf2eb,#0d695e)';
  $('legend-low').textContent=diverge?format(-limit):'0';$('legend-high').textContent=format(limit);
  $('legend-note').textContent=`${metric.unit} · ${diverge?(compare?'blue = lower in selected scenario; gold = higher in selected scenario':'blue = net importer; gold = net exporter'):'darker green = higher value'}`;
  const params=new URLSearchParams({metric:state.metric,year:state.year,scenario:state.scenario,compare:state.compare,view:state.view});
  if(state.region)params.set('region',state.region);history.replaceState(null,'',`?${params}`);
}
async function init(){
  const params=new URLSearchParams(location.search);
  for(const id of ['metric','year','scenario','compare']){
    if(params.has(id)&&[...$(id).options].some(o=>o.value===params.get(id)))$(id).value=params.get(id);
    state[id]=$(id).value;$(id).addEventListener('change',()=>{state[id]=$(id).value;render()});
  }
  if(['map','bars'].includes(params.get('view')))state.view=params.get('view');
  $('map-tab').addEventListener('click',()=>{state.view='map';render()});$('bars-tab').addEventListener('click',()=>{state.view='bars';render()});
  $('share').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(location.href);$('share').textContent='Link copied';setTimeout(()=>$('share').textContent='Copy chart link',1800)}catch{$('share').textContent='Copy URL from address bar'}});
  try{
    const [csv,geo]=await Promise.all([fetch('data/elote-regions.csv'),fetch('data/elote-regions.geojson')]);
    if(!csv.ok||!geo.ok)throw new Error('A data file could not be loaded.');
    const rows=parseCSV(await csv.text());geography=await geo.json();
    for(const row of rows)records.set(key(row.scenario,row.year,row.region),row);
    regions=[...new Set(rows.map(r=>r.region))].sort();
    if(regions.includes(params.get('region')))state.region=params.get('region');render();
  }catch(error){$('error').hidden=false;$('error').textContent=`Dashboard unavailable: ${error.message}`;$('map-panel').hidden=true}
}
init();
