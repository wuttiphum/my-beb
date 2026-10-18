import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {packHeartWords} from '../dist/heart-layout.mjs';

const asset=name=>JSON.parse(readFileSync(new URL('../dist/assets/'+name,import.meta.url),'utf8'));
const data=asset('animation-data.json'),metrics=asset('tk-typography.json').fillMetrics['9'];
const outline=Array.from({length:201},(_,i)=>{const t=i/200*Math.PI*2;return[16*Math.sin(t)**3,13*Math.cos(t)-5*Math.cos(2*t)-2*Math.cos(3*t)-Math.cos(4*t)]});
const words=packHeartWords({outline,metrics,phrases:data.phrases,names:['อัง','Ang','Nathaiinee Samoeton','Ang','อัง']});
const rows=[...new Set(words.map(w=>w.y))],half=metrics.linespace/18.5/2;
// Independent point-in-polygon check, rather than repeating interval clipping.
function inside(x,y){let hit=false;for(let i=0,j=outline.length-1;i<outline.length;j=i++){const[a,b]=outline[i],[c,d]=outline[j];if((b>y)!==(d>y)&&x<(c-a)*(y-b)/(d-b)+a)hit=!hit}return hit}

test('fills both lobes on the row below the notch',()=>{
 const y=rows.reduce((best,v)=>Math.abs(v-5)<Math.abs(best-5)?v:best,rows[0]);
 const row=words.filter(w=>w.y===y);
 assert.ok(row.some(w=>w.x<-4),'Left lobe has a full blank row below the heart notch');
 assert.ok(row.some(w=>w.x>4),'Right lobe has a full blank row below the heart notch');
});

test('does not skip any wide interior region on a text row',()=>{
 for(const y of rows){
  const runs=[];let start=null;
  for(let x=-16;x<=16.1;x+=.1){
   const safe=inside(x,y-half)&&inside(x,y)&&inside(x,y+half);
   if(safe&&start===null)start=x;
   if(!safe&&start!==null){runs.push([start,x-.1]);start=null}
  }
  for(const[left,right]of runs.filter(([a,b])=>b-a>3))assert.ok(words.some(w=>w.y===y&&w.x>left&&w.x<right),`Empty region at y=${y}, x=${left}..${right}`);
 }
});

test('every word stays inside the heart, including the concave notch',()=>{
 for(const word of words){
  for(let step=0;step<=10;step++)for(const y of[word.y-half,word.y,word.y+half]){
   const x=word.x-word.width/2+word.width*step/10;
   assert.ok(inside(x,y),`Text outside heart: ${word.value} at ${x},${y}`);
  }
 }
});

test('words on a row do not overlap and all twenty languages remain',()=>{
 for(const y of rows){const row=words.filter(w=>w.y===y).sort((a,b)=>a.x-b.x);for(let i=1;i<row.length;i++)assert.ok(row[i].x-row[i].width/2-(row[i-1].x+row[i-1].width/2)>.44)}
 assert.equal(new Set(words.filter(w=>data.phrases.includes(w.value)).map(w=>w.value)).size,20);
});
