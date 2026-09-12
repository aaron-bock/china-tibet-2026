import fs from 'node:fs';
const U='/root/.claude/uploads/3fe8de66-d4b8-58ea-b27e-35ac9d3f802e/';
const pl = fs.readFileSync(U+'085eebfd-Packing-List.html','utf8').split('\n');
const pc = fs.readFileSync(U+'f34bae0e-Prep-Checklist.html','utf8').split('\n');

// Packing List: BAGS (217) .. SECTIONS close
let s = pl.findIndex(l=>l.startsWith('const BAGS = ['));
let e = pl.findIndex((l,i)=>i>s && l.trim()==='];' && pl.slice(s,i).join('\n').includes('const SECTIONS'));
const plSrc = pl.slice(s, e+1).join('\n');
const plOut = new Function(plSrc + '\nreturn {BAGS,CLIMATE,SECTIONS};')();

// Prep Checklist: GEAR, CHINA, TASKS, LEAVE
let g = pc.findIndex(l=>l.startsWith('const GEAR = ['));
let lv = pc.findIndex(l=>l.startsWith('const LEAVE = ['));
const pcSrc = pc.slice(g, lv+1).join('\n');
const pcOut = new Function(pcSrc + '\nreturn {GEAR,CHINA,TASKS,LEAVE};')();

fs.writeFileSync('extracted.json', JSON.stringify({...plOut, ...pcOut}, null, 1));
const n = plOut.SECTIONS.reduce((a,x)=>a+x.items.length,0);
console.log('packing sections:', plOut.SECTIONS.length, '| items:', n);
console.log('bags:', plOut.BAGS.length, '| climate:', plOut.CLIMATE.length);
console.log('prep gear groups:', pcOut.GEAR.length, '| gear items:', pcOut.GEAR.reduce((a,x)=>a+x[1].length,0));
console.log('china:', pcOut.CHINA.length, '| tasks:', pcOut.TASKS.length, '| leave:', pcOut.LEAVE.length);
console.log('\nsection titles:');
plOut.SECTIONS.forEach(x=>console.log(' -', x.t, x.special?('['+x.special+']'):'', x.items.length));
