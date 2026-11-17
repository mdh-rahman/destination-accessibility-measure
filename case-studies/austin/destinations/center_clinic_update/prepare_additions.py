import json, pathlib, urllib.request, urllib.parse
p=pathlib.Path(__file__).parent
rows=[
('ch_southeast','Central Health Southeast Health & Wellness Center','2901 Montopolis Dr','Austin','78741','primary_convenient_clinic','Community resources; wellness; primary and convenient care',True,True),
('ch_northeast','Central Health Northeast Health & Resource Center','6711 Johnny Morris Rd','Austin','78724','community_resource_center','Benefits assistance; some services temporarily unavailable during construction',True,False),
('ch_hornsby','Central Health Hornsby Bend Health & Wellness Center','3700 Gilbert Rd','Austin','78725','primary_care_clinic','Community rooms; wellness; primary care',True,True),
('ch_delvalle','Central Health Del Valle Health & Wellness Center','7050 Elroy Rd','Del Valle','78617','primary_care_clinic','Community resources; primary care; wellness',True,True),
('ch_education','Central Health Clinical Education Center','1400 N Interstate 35','Austin','78701','specialty_rehabilitation_clinic','Third floor; rehabilitation and clinical services. Community category included by project decision; not verified as general recreation.',True,True),
('ch_east','Central Health East Austin Specialty Clinic','211 Comal St','Austin','78702','specialty_clinic','Specialty outpatient services; eligibility and appointments apply',False,True),
('ch_capital','Central Health Capital Plaza Specialty Clinic','5339 N Interstate 35 Ste 100','Austin','78723','specialty_clinic','Specialty outpatient services; eligibility and appointments apply',False,True),
('ch_rosewood','Central Health Rosewood-Zaragosa Specialty Clinic','2802 Webberville Rd','Austin','78702','specialty_clinic','Referral-based specialty services for MAP members',False,True),
('cuc_hancock','CommUnityCare Hancock Health Center','1000 E 41st St Ste 700','Austin','78751','convenient_care','Existing convenient-care clinic; not future Central Health Hancock redevelopment',False,True),
('lsc_jonestown','Lone Star Circle of Care - Jonestown','18220 FM 1431 Ste D','Jonestown','78641','convenient_care','Convenient care listed by Central Health',False,True)]
out=[]
for vals in rows:
 d=dict(zip(['facility_id','facility_name','address','city','zip','facility_type','notes','community','clinic'],vals))
 d['source_url']='https://www.centralhealth.net/'+('urgent-and-emergency-care/' if d['facility_id'] in ['cuc_hancock','lsc_jonestown'] else 'clinical-services/locations/')
 cache=p/(d['facility_id']+'_geocode.json')
 if not cache.exists():
  args=urllib.parse.urlencode(dict(SingleLine=f"{d['address']}, {d['city']}, TX {d['zip']}",f='json',outFields='Match_addr,Addr_type',maxLocations=3))
  with urllib.request.urlopen('https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?'+args,timeout=45) as r: cache.write_bytes(r.read())
 c=json.loads(cache.read_text())['candidates'][0]
 d.update(longitude=c['location']['x'],latitude=c['location']['y'],geocode_score=c['score'],geocode_type=c['attributes']['Addr_type'],matched_address=c['address'])
 assert c['score']>=95 and c['attributes']['Addr_type'] in ['PointAddress','Subaddress'],d
 out.append(d)
(p/'additions.json').write_text(json.dumps(out,indent=2))
print([(d['facility_id'],d['geocode_score'],d['matched_address']) for d in out])
