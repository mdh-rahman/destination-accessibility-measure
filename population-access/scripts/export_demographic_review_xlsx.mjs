import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';
const root=process.argv[2], kind=process.argv[3];
const dir=path.join(root,'population-access/output/demographic-review');
const cache=path.join(root,'case-studies/austin/data/raw/population_access/review_expanded');
await fs.mkdir('/tmp/demographic-review-build',{recursive:true});
const payload=JSON.parse(await fs.readFile(path.join(cache,`review_${kind}.json`),'utf8'));
const dictionary=JSON.parse(await fs.readFile(path.join(cache,'review_dictionary.json'),'utf8'));
const checks=JSON.parse(await fs.readFile(path.join(cache,'review_checks.json'),'utf8'));
const notes=(await fs.readFile(path.join(dir,'README.txt'),'utf8')).trim().split('\n');
const wb=Workbook.create();
function col(n){let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;}
function table(name,heads,rows){
 const s=wb.worksheets.add(name);s.showGridLines=false;
 s.getRangeByIndexes(0,0,1,heads.length).values=[heads];
 for(let i=0;i<rows.length;i+=500)s.getRangeByIndexes(i+1,0,Math.min(500,rows.length-i),heads.length).values=rows.slice(i,i+500);
 const range=s.getRangeByIndexes(0,0,rows.length+1,heads.length);
 range.format.font={name:'Arial',size:10};range.format.rowHeight=18;range.format.columnWidth=22;range.format.verticalAlignment='center';
 const h=s.getRangeByIndexes(0,0,1,heads.length);h.format.fill='#18384B';h.format.font={name:'Arial',size:10,bold:true,color:'#FFFFFF'};h.format.wrapText=true;h.format.rowHeight=58;
 s.freezePanes.freezeRows(1);s.freezePanes.freezeColumns(1);
 s.tables.add(`A1:${col(heads.length-1)}${rows.length+1}`,true,name.replace(/ /g,'')+'Table').style='TableStyleMedium2';
 return s;
}
const data=table('Data',payload.columns,payload.data);
data.tabColor='#18384B';
payload.columns.forEach((c,j)=>{
 const r=data.getRangeByIndexes(1,j,payload.data.length,1);
 if(['geoid','h3_id','county_fips','tract_geoid'].includes(c)){r.setNumberFormat(c==='h3_id'?'@':'0');data.getRange(`${col(j)}1`).format.columnWidth=22;}
 else if(c==='name'){data.getRange(`${col(j)}1`).format.columnWidth=52;}
 else if(c.endsWith('_pct'))r.setNumberFormat('0.0"%"');
 else if(c==='latitude'||c==='longitude')r.setNumberFormat('0.00000');
 else if(c==='area_sq_km')r.setNumberFormat('0.00');
 else if(payload.data.some(row=>typeof row[j]==='number'))r.setNumberFormat(kind==='h3_r8'?'#,##0.0':'#,##0');
});
const dh=Object.keys(dictionary[0]);const ds=table('Variable dictionary',dh,dictionary.map(r=>dh.map(k=>r[k]??null)));
ds.getRange('A1:H1').format.rowHeight=30;
for(const [c,w] of Object.entries({A:35,B:58,C:14,D:34,E:65,F:26,G:90,H:65}))ds.getRange(`${c}1`).format.columnWidth=w;
ds.getRange(`A2:H${dictionary.length+1}`).format.wrapText=true;
ds.getRange(`A2:H${dictionary.length+1}`).format.rowHeight=72;
const qh=Object.keys(checks[0]);const qs=table('Allocation checks',qh,checks.map(r=>qh.map(k=>r[k]??null)));
qs.getRange(`C2:G${checks.length+1}`).setNumberFormat('#,##0.000');qs.getRange('A1').format.columnWidth=38;
const readme=wb.worksheets.add('Read me');readme.showGridLines=false;readme.tabColor='#9FAEB7';
readme.getRange(`A1:A${notes.length}`).values=notes.map(x=>[x]);readme.getRange(`A1:A${notes.length}`).format={font:{name:'Arial',size:11},columnWidth:125,rowHeight:34,wrapText:true};readme.getRange('A1').format.font={name:'Arial',size:14,bold:true,color:'#18384B'};
const sourceRows=[['Field convention','Meaning'],['base variable','Estimated count; see dictionary for unit and universe'],['_pct','Percentage, numeric scale 0 to 100; blank when denominator is zero or unavailable'],['_moe','90% ACS count margin of error; root-sum-of-squares approximation for derived counts'],['H3 uncertainty','No H3 MOEs: allocation uncertainty is not captured by source ACS margins of error'],['Tract-only fields','Disability and immigration variables are blank in block-group data; see dictionary']];
readme.getRange(`A${notes.length+3}:B${notes.length+8}`).values=sourceRows;
readme.getRange(`A${notes.length+3}:B${notes.length+8}`).format.wrapText=true;readme.getRange(`B${notes.length+3}`).format.columnWidth=90;
console.log(`${kind}: populated ${payload.data.length} rows and ${payload.columns.length} columns`);
wb.recalculate();
console.log((await wb.inspect({kind:'region',sheetId:'Data',range:'A1:D3',maxChars:600,tableMaxRows:3,tableMaxCols:4})).ndjson);
for(const [sheet,range] of [['Data','A1:F8'],['Variable dictionary','A1:D7'],['Allocation checks','A1:D7'],['Read me','A1:A9']]){
 const preview=await wb.render({sheetName:sheet,range,scale:1,format:'png'});
 await fs.writeFile(`/tmp/demographic-review-build/${kind}-${sheet.replaceAll(' ','_')}.png`,new Uint8Array(await preview.arrayBuffer()));
}
const file=await SpreadsheetFile.exportXlsx(wb);await file.save(path.join(dir,`austin_metro_demographics_${kind}.xlsx`));
console.log(`${kind}: exported`);
