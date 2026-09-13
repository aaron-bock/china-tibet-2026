# -*- coding: utf-8 -*-
"""Rebuild trip/packing as a list of things, each appearing exactly once.

Three rules, from Aaron:
  1. Every row is an ITEM, not an action and not what the item is for.
  2. Nothing appears twice.
  3. No "buy in China" rows and no "leave at home" rows.

Context categories (On the Z165, Base camp night, Disneyland) are dissolved:
they described what an item was FOR, which is what the Legs column already
does. What survives is ten categories of thing.
"""
import json, collections

src=json.load(open("live4/trip/packing.json",encoding="utf-8"))
old={i["id"]:i for i in src["items"]}

# (id, new name, group, bag, zone, [absorbed ids], appended Why)
KEEP=[
# ---- Bags & packing ----
("pk001","Away The Large","Bags & packing","Away","All legs",["pk152"],
 "Do NOT use the expansion zipper — an expanded case is over most carriers' checked dimensions and the Z165 luggage space is not generous."),
("pk002","Osprey Talon 44","Bags & packing","Talon 44","All legs",[],""),
("pk003","Osprey daypack","Bags & packing","Daypack","Tibet · Disney",["pk143"],
 "Still to pick which one comes. It is the bag for park days and for the EBC eco-bus — the Talon stays at the hotel on Disney days."),
("pk004","REI Ruckpack Waistpack","Bags & packing","Sling","All legs",["pk144"],
 "Worn crossbody, and the one bag that never leaves you — including on the coasters, where a shoulder bag is a problem."),
("pk005","Luggage scale","Bags & packing","Talon 44","All legs",[],""),
("pk006","Packing cubes","Bags & packing","Away → Talon 44","All legs",[],""),
("pk007","Raincover for the Talon","Bags & packing","Talon 44","Tibet · EBC night",[],""),
("pk008","Compression sack","Bags & packing","Talon 44","EBC night",[],""),
("pk009","Dry bags and ziplocks","Bags & packing","Away","Tibet",[],""),
("pk010","Padlock and cable","Bags & packing","Talon 44","Z165",[],""),
("pk011","Detergent sheets","Bags & packing","Away","All legs",[],""),
("pk012","Luggage tags","Bags & packing","Away","All legs",[],""),
# ---- Documents & money ----
("pk025","Passport","Documents & money","Sling","All legs",["pk103","pk131"],
 "Lives in the sling, never the pack: it is the Z165 boarding pass, the Tibet permit check and your real-name Disney ticket, so it comes out several times a day."),
("pk026","Tibet Travel Permit","Documents & money","Sling","Tibet",[],""),
("pk027","Printed bookings","Documents & money","Talon 44","All legs",["pk130"],
 "Flights, hotels, the tour receipt and the day-by-day on paper — the copy that still works with a dead phone behind the firewall."),
("pk028","Offline document copies","Documents & money","Sling","All legs",[],""),
("pk029","Credit and debit cards","Documents & money","Sling","All legs",[],""),
("pk030","Chinese cash","Documents & money","Sling","Tibet",[],""),
("pk031","Tip envelopes","Documents & money","Talon 44","Tibet",[],""),
("pk032","USD emergency reserve","Documents & money","Away","All legs",[],""),
("pk033","Passport photos ×4","Documents & money","Talon 44","All legs",[],""),
("pk034","Insurance details","Documents & money","Sling","All legs",[],""),
("pk035","Contacts card","Documents & money","Sling","All legs",[],""),
("pk036","Hotel addresses in Chinese","Documents & money","Sling","Xi'an · Shanghai",[],""),
("pk037","Arc'teryx Mantis 1","Documents & money","On you","All legs",[],""),
# ---- Clothing ----
("pk057","Merino base layer tops ×2","Clothing","Away → Talon 44","Tibet · EBC night",[],""),
("pk058","Merino long johns ×2","Clothing","Away → Talon 44","EBC night",[],""),
("pk059","Midweight fleece","Clothing","Away → Talon 44","Tibet · EBC night",[],""),
("pk060","Down puffy","Clothing","Talon 44","Tibet · EBC night",[],""),
("pk061","Hardshell jacket","Clothing","On you","All legs",[],""),
("pk062","Waterproof overtrousers","Clothing","Away → Talon 44","EBC night",[],""),
("pk063","Trekking trousers ×2","Clothing","Away","Tibet · EBC night",[],""),
("pk064","Jeans ×1","Clothing","Away","Xi'an · Shanghai",[],""),
("pk065","T-shirts and casual shirts ×4","Clothing","Away","Xi'an · Shanghai",[],""),
("pk066","Collared shirt","Clothing","Away","Shanghai",[],""),
("pk067","Underwear ×8–10","Clothing","Away","All legs",[],""),
("pk068","Hiking socks ×5","Clothing","Away","Tibet · Disney",["pk138"],
 "Also the Disney answer: a dry pair in the day bag on a 20,000-step day is the difference between finishing the evening and not."),
("pk069","Heavy wool socks ×2","Clothing","Away → Talon 44","EBC night",[],""),
("pk070","Warm hat","Clothing","Talon 44","Tibet · EBC night",[],""),
("pk071","Brimmed sun hat","Clothing","Daypack","Tibet · Disney",[],
 "Plateau sun at 5,000 m and a full day queueing in Shanghai are the same problem."),
("pk072","Buff or neck gaiter ×2","Clothing","Sling","Tibet · EBC night",[],""),
("pk073","Liner and insulated gloves","Clothing","Talon 44","EBC night",[],""),
("pk074","Sunglasses","Clothing","Sling","Tibet · EBC night",[],""),
("pk075","Sleepwear","Clothing","Talon 44","Z165 · Tibet",[],""),
("pk076","Swimsuit","Clothing","Away","Xi'an · Shanghai",[],""),
("pk077","Light jacket","Clothing","Away","Shanghai · Disney",["pk140"],
 "Doubles as the park layer — something you can take off at midday and stuff in the day bag."),
("pk127","Modest clothes","Clothing","Away","Tibet",[],""),
("pk139","Packable rain poncho","Clothing","Daypack","Disney",[],""),
# ---- Footwear ----
("pk078","Hiking boots","Footwear","On you","Tibet · EBC night",["pk153"],
 "Worn in before you fly. New boots on the plateau is how a trip gets ruined in the first two days, and there is no fixing it once you are up there."),
("pk079","City walking shoes","Footwear","Away","Xi'an · Shanghai · Disney",["pk136"],
 "The second pair matters on the park days: alternating shoes across three 20,000-step days is worth more than any insole."),
("pk080","Slides","Footwear","Talon 44","Z165 · EBC night",["pk014"],
 "Train corridor, the tent camp and any shared shower. Cheap to pick up in Xi'an if you would rather not pack them."),
("pk081","Warm insoles","Footwear","Away → Talon 44","EBC night",[],""),
# ---- Medical & altitude ----
("pk038","Altitude medication","Medical & altitude","Sling","Tibet · EBC night",[],""),
("pk039","Pulse oximeter","Medical & altitude","Talon 44","EBC night",[],""),
("pk040","Ibuprofen and acetaminophen","Medical & altitude","Talon 44","All legs",[],""),
("pk041","Anti-nausea tablets","Medical & altitude","Talon 44","EBC night",[],""),
("pk042","Motion sickness tablets","Medical & altitude","Sling","Tibet",[],""),
("pk043","Loperamide and rehydration salts","Medical & altitude","Talon 44","All legs",[],""),
("pk044","Electrolyte tablets","Medical & altitude","Talon 44","Tibet · EBC night",[],""),
("pk045","Prescription medication","Medical & altitude","Talon 44","All legs",[],""),
("pk046","Throat lozenges","Medical & altitude","Sling","Tibet · EBC night",[],""),
("pk047","Saline nasal spray","Medical & altitude","Talon 44","Tibet · EBC night",[],""),
("pk048","Sunscreen SPF 50","Medical & altitude","Away","Tibet · EBC night · Disney",["pk146"],
 "Large tube checked, small tube on you. The park days need it as much as the plateau does."),
("pk049","Lip balm with SPF","Medical & altitude","Sling","Tibet · EBC night",[],""),
("pk050","Eye drops","Medical & altitude","Sling","Tibet · EBC night",[],""),
("pk051","Blister kit","Medical & altitude","Daypack","Tibet · Disney",["pk137"],
 "In your pocket, not the hotel room — a hotspot at 11:00 is a blister by 14:00 either at base camp or in a queue."),
("pk052","First aid kit","Medical & altitude","Talon 44","All legs",[],""),
("pk053","Hand sanitiser","Medical & altitude","Sling","All legs",[],""),
("pk055","Melatonin","Medical & altitude","Talon 44","All legs",[],""),
("pk056","Multivitamin","Medical & altitude","Away","All legs",[],""),
# ---- Toiletries ----
("pk094","Toothbrush and toothpaste","Toiletries","Talon 44","All legs",[],""),
("pk095","Moisturiser and hand cream","Toiletries","Away","Tibet · EBC night",[],""),
("pk096","No-rinse body wipes","Toiletries","Away → Talon 44","EBC night",[],""),
("pk097","Wet wipes and tissues","Toiletries","Sling","All legs",["pk054","pk016"],
 "Carry a packet at all times: public toilets rarely supply paper. Restock in bulk once you are there rather than flying a month's worth in."),
("pk098","Quick-dry towel","Toiletries","Away → Talon 44","EBC night",[],""),
("pk099","Deodorant, soap, shampoo","Toiletries","Away","All legs",["pk017"],
 "Travel sizes only — full-size bottles are cheap and everywhere once you land."),
("pk100","Razor and nail clippers","Toiletries","Away","All legs",[],""),
("pk101","Glasses and contacts","Toiletries","Talon 44","Tibet · EBC night",[],""),
("pk102","Face masks","Toiletries","Sling","All legs",[],""),
("pk116","Toilet paper","Toiletries","Sling","Tibet · EBC night",[],
 "A part-roll in a pocket. There is no paper at the base camp toilets and none on most of the drive."),
# ---- Electronics ----
("pk082","Phone","Electronics","Sling","All legs",[],
 "Worth bringing your old handset as a backup too — it is your ticket, your wallet and your only map."),
("pk083","20,000 mAh power bank","Electronics","Talon 44","Z165 · EBC night · Disney",["pk013","pk084","pk133","pk151"],
 "BUY THIS IN XI'AN, do not fly one in. China requires a moulded 3C mark that no US-market battery carries, lithium cannot go in the hold, and an uncertified pack is confiscated at Lhasa on the way to Shanghai. Assume no reliable power on the Z165, none at the tent camp, and a full day off-charger at the park."),
("pk085","Multi-port charger and cables","Electronics","Talon 44","All legs",[],""),
("pk086","Plug adapters ×2","Electronics","Talon 44","All legs",[],""),
("pk087","Headlamp","Electronics","Talon 44","EBC night",["pk022"],
 "With spare batteries — easy to pick up there rather than pack."),
("pk088","Camera","Electronics","Daypack","All legs",[],""),
("pk089","Earplugs and eye mask","Electronics","Talon 44","Z165 · EBC night",[],""),
("pk090","Headphones","Electronics","Sling","Z165",[],""),
("pk091","Kindle or a paperback","Electronics","Talon 44","Z165",[],""),
("pk092","Watch","Electronics","On you","EBC night",[],""),
("pk093","Travel eSIM","Electronics","Sling","All legs",["pk132"],
 "Installed BEFORE you fly — it cannot be downloaded from inside the firewall. It is also what keeps you connected through a full park day, when the ticket, the queue times and the wallet are all on the phone."),
("pk145","Phone strap or lanyard","Electronics","Sling","Disney",[],""),
# ---- Trek & camp gear ----
("pk111","Sleeping bag liner","Trek & camp gear","Talon 44","EBC night",[],""),
("pk020","Sleeping bag","Trek & camp gear","Buy or rent there","EBC night",[],
 "Rated to about −10 °C. Rent it in Lhasa rather than carrying one across three cities — but it is a real decision, so it stays on the list."),
("pk021","Trekking poles","Trek & camp gear","Buy or rent there","Tibet · EBC night",[],
 "Rent in Lhasa. Only worth it if you intend to walk beyond the base camp marker."),
("pk019","Heavy down parka","Trek & camp gear","Buy or rent there","EBC night",[],
 "Rent or buy around Barkhor in Lhasa. Cheaper and warmer than anything you would pack, and you hand it back."),
("pk112","Hand and toe warmers","Trek & camp gear","Talon 44","EBC night",[],""),
# ---- Food & water ----
("pk121","Snacks","Food & water","Talon 44","Z165 · Tibet · EBC night · Disney",["pk104","pk115","pk142","pk023"],
 "One stock, four jobs: thirty hours on the Z165, the drive days, the tent night where dinner is basic and early, and the park, where a queue is a bad place to be hungry. Buy the bulk of it in Xi'an."),
("pk122","Instant oatmeal and soup sachets","Food & water","Talon 44","Z165 · EBC night",[],""),
("pk107","Instant coffee or tea sachets","Food & water","Talon 44","Z165",[],""),
("pk123","Chopsticks or a spork","Food & water","Talon 44","Z165",[],""),
("pk120","Water purification tablets","Food & water","Talon 44","EBC night",[],""),
("pk141","Refillable water bottle","Food & water","Daypack","EBC night · Disney",["pk113"],
 "A wide-mouth one doubles as a hot-water bottle in the tent, filled from the camp thermos."),
("pk105","Insulated thermos","Food & water","Talon 44","Z165 · Tibet",["pk015"],""),
# ---- Small things ----
("pk124","Small gifts from home","Small things","Away","All legs",["pk110"],
 "Also the answer to the soft-sleeper cabin: something small to hand over goes a long way across thirty hours and no shared language."),
("pk126","Small-denomination notes","Small things","Sling","Tibet",[],""),
("pk128","Notebook and pen","Small things","Sling","All legs",[],""),
("pk129","Duct tape and zip ties","Small things","Talon 44","All legs",[],""),
("pk108","Neck pillow","Small things","Talon 44","Z165",[],""),
]

DROP={
 "pk109":"instruction, not an item (board 30 minutes early)",
 "pk114":"instruction (charge everything before the tent night)",
 "pk117":"instruction (no shower, alcohol or sleeping pill at altitude)",
 "pk118":"instruction (get up for sunrise)",
 "pk135":"action (decide on Premier Access) — lives in Disneyland",
 "pk147":"instruction (arrive before opening)",
 "pk134":"not a packing item (Alipay funded) — lives in Apps & wallet",
 "pk119":"rule, not an item (bottled water only) — lives in the itinerary",
 "pk106":"buy there (two litres before boarding)",
 "pk125":"buy there (umbrella)",
 "pk018":"buy there (oxygen cans)",
 "pk024":"buy there (holdall for the way home)",
 "pk149":"prohibition (no drone) — moved to Reference",
 "pk150":"prohibition (no political material) — moved to Reference",
 "pk154":"prohibition (no valuables) — moved to Reference",
}

MERGE_ORDER=["own","buy","skip"]
out=[]
absorbed_all=set()
for (pid,name,group,bag,zone,absorbs,extra) in KEEP:
    base=dict(old[pid])
    absorbed_all.update(absorbs)
    own=base.get("own") or ""
    prio=base.get("prio") or ""
    for aid in absorbs:
        a=old[aid]
        if not own and a.get("own"): own=a["own"]
        if a.get("prio")=="must": prio="must"
    row={"id":pid,"item":name,"group":group,"bag":bag,"zone":zone}
    if own: row["own"]=own
    if prio: row["prio"]=prio
    det=(base.get("detail") or "").strip()
    if extra: det=(det+" " if det else "")+extra
    row["detail"]=det
    out.append(row)

GROUPS=["Bags & packing","Documents & money","Clothing","Footwear","Medical & altitude",
        "Toiletries","Electronics","Trek & camp gear","Food & water","Small things"]
pos={r["id"]:n for n,r in enumerate(out)}           # KEEP order, captured before sorting
out.sort(key=lambda r:(GROUPS.index(r["group"]), pos[r["id"]]))

kept={r["id"] for r in out}
missing=[i for i in old if i not in kept and i not in absorbed_all and i not in DROP]
assert not missing, "unaccounted: "+str(missing)
names=[r["item"] for r in out]
dupe=[n for n,c in collections.Counter(names).items() if c>1]
assert not dupe, "duplicate names: "+str(dupe)

before=collections.Counter(i.get("own") for i in src["items"])
after=collections.Counter(r.get("own") for r in out)
print("items  %d -> %d" % (len(src["items"]), len(out)))
print("groups %d -> %d" % (len({i.get('group') for i in src['items']}), len(GROUPS)))
print("marks  before", dict(before), "\n       after ", dict(after))
print("must   %d -> %d" % (sum(1 for i in src["items"] if i.get("prio")=="must"), sum(1 for r in out if r.get("prio")=="must")))
print("\nabsorbed %d, dropped %d" % (len(absorbed_all), len(DROP)))
json.dump({"items":out}, open("out/packing.json","w",encoding="utf-8"), ensure_ascii=False)
