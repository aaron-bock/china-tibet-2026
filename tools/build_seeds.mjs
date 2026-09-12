import fs from 'node:fs';
const d = JSON.parse(fs.readFileSync('extracted.json','utf8'));
const ZONE={ALL:"All legs",XIAN:"Xi'an",TRAIN:"Z165",TIBET:"Tibet",EBC:"EBC night",SHANGHAI:"Shanghai",DISNEY:"Disney"};
const BAG={AWAY:"Away",TALON:"Talon 44",DAY:"Daypack",SLING:"Sling",WEAR:"On you",BUY:"Buy there"};
const SHORT={
 "Before you fly":"Before you fly","The four bags":"Bags & packing",
 "Buy it in China, not at home":"Buy in China","Documents and money":"Documents & money",
 "Altitude and the medical kit":"Altitude & medical","Clothing — the layering system":"Clothing",
 "Footwear":"Footwear","Electronics and power":"Electronics","Toiletries and washing":"Toiletries",
 "Thirty hours on the Z165":"On the Z165","The base camp night":"Base camp night",
 "Food, water and the stomach":"Food & water","Small things that make China easier":"Small things",
 "Shanghai Disneyland":"Disneyland","Leave at home":"Leave at home"};
const id=(p,i)=>p+String(i).padStart(3,"0");

/* ---- packing: every SECTIONS item except the PREP list and the FLOW narrative ---- */
const pack=[]; let pi=0;
for(const s of d.SECTIONS){
  if(s.special==="PREP"||s.special==="FLOW") continue;
  for(const it of s.items){
    const bag = it.b ? BAG[it.b]+(it.mv?" → "+BAG[it.mv]:"") : "";
    pack.push({
      id:id("pk",++pi), item:it.n, group:SHORT[s.t]||s.t,
      status: s.special==="LEAVE" ? "action" : (it.crit?"action":"pending"),
      bag, zone:(it.z||[]).map(z=>ZONE[z]||z).join(" · "),
      detail: it.note||""
    });
  }
}
fs.writeFileSync('seed/packing.json', JSON.stringify({items:pack},null,1));

/* ---- kit: the four bags, the six repacks, the five climates ---- */
const kit=[]; let ki=0;
for(const b of d.BAGS) kit.push({id:id("kt",++ki),name:b.name,kind:"Bag",spec:b.spec,detail:b.role});
const flow=d.SECTIONS.find(s=>s.special==="FLOW");
if(flow&&flow.cal) for(const blk of flow.cal) (blk.ol||[]).forEach((step,n)=>
  kit.push({id:id("kt",++ki),name:step[0],kind:"Repack "+(n+1),spec:"",detail:step[1]}));
for(const c of d.CLIMATE) kit.push({id:id("kt",++ki),name:c.name,kind:"Weather",spec:c.when+" · "+c.temp,detail:c.note});
fs.writeFileSync('seed/kit.json', JSON.stringify({items:kit},null,1));

/* ---- tasks: the packing list's current PREP list, plus the items only my dossier had ---- */
const prep=d.SECTIONS.find(s=>s.special==="PREP");
const tasks=[]; let ti=0;
for(const it of prep.items) tasks.push({
  id:id("tk",++ti), title:it.n, owner:"Aaron",
  status: it.crit?"action":"pending",
  due:(it.z||[]).map(z=>ZONE[z]||z).join(" · ")||"before you fly",
  detail: it.note||""
});
const mine=JSON.parse(fs.readFileSync('seed/tasks.json','utf8')).items;
const KEEP=new Set(["t4","t5","t6","t7","t8","t9","t12","t13"]);
for(const t of mine) if(KEEP.has(t.id)) tasks.push({...t, id:id("tk",++ti)});
fs.writeFileSync('seed/tasks.json', JSON.stringify({items:tasks},null,1));

console.log("packing:",pack.length,"| kit:",kit.length,"| tasks:",tasks.length);
console.log("packing groups:",[...new Set(pack.map(p=>p.group))].join(" / "));
console.log("crit/key packing items:",pack.filter(p=>p.status==="action").length);
