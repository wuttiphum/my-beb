// Pack measured text in fixed heart coordinates; projection belongs to app.js.
const REFERENCE_SCALE=18.5;
function spans(y,outline){let cross=[];for(let i=1;i<outline.length;i++){let [x1,y1]=outline[i-1],[x2,y2]=outline[i];if((y1<=y&&y<y2)||(y2<=y&&y<y1))cross.push(x1+(y-y1)*(x2-x1)/(y2-y1))}cross.sort((a,b)=>a-b);let out=[];for(let i=0;i+1<cross.length;i+=2)out.push([cross[i],cross[i+1]]);return out}

export function packHeartWords({outline,metrics,phrases,names}){
 const measure=value=>metrics.widths[value]/REFERENCE_SCALE;
 const half=metrics.linespace/REFERENCE_SCALE/2,words=[];
 let pi=0,ni=0;
 for(let y=Math.max(...outline.map(p=>p[1]))-half-.5;y>-17+half+.5;y-=half*2+.28){
  for(const span of spans(y,outline)){
   let segments=[span];
   for(const edgeY of[y-half,y+half]){
    // A row can be connected at its center but split into two lobes at its
    // top edge. Keep every safe intersection, not just the longest lobe.
    const edges=spans(edgeY,outline);
    segments=segments.flatMap(([a,b])=>edges.map(([c,d])=>[Math.max(a,c),Math.min(b,d)]).filter(([a,b])=>a<b));
   }
   for(let[left,right]of segments){
    let x=left+.55;right-=.55;
    while(x<right){
     const phrase=phrases[pi%phrases.length];let value=words.length%2===0?phrase:names[ni%names.length],width=measure(value);
     if(x+width>right){value=ni%2?'Ang':'อัง';width=measure(value)}
     if(x+width>right)break;
     words.push({x:x+width/2,y,value,width});if(value===phrase)pi++;else ni++;x+=width+.45;
    }
   }
  }
 }
 return words;
}
