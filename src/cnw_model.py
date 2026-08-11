#!/usr/bin/env python3
# Compute Net Worth Index v1 — master dataset + model
# compute.world | compiled 2026-08-09
#
# Row fields:
# (name, region, land_km2, pop_M, gdp_B, cpi, stab, sanc, gpu, mom, ll, fib, grid, cool, seis, wat,
#  h_tech, h_feas, h_dev, geo_res, geo_dev, s_class, wind, gas, exp_twh, flag, note)
# stab: H/M/L/C  fib,grid: S/M/W  cool: C/M/H  seis,wat: H/M/L  s_class: E/H/M/L/0
# h_feas None -> 0.6*h_tech. flag: V=sourced, E=estimate/derived, P=provisional/n.v.
# EST-CF045 = TWh/yr figure converted to nameplate GW at capacity factor 0.45 (GW = TWh/3.942)

import json, csv

R = [
# --- South Asia ---
("Nepal","South Asia",147181,30,45,34,"M",0,0.80,0.6,1,"M","M","M","H","M",83.0,42.1,3.4,0,0,"H",0,0,3.9,"V","83 GW theoretical (WECS/Shrestha) / 42.1 GW econ feasible; exports 3.877 TWh FY25/26 at ~NPR 7.56/kWh"),
("Bhutan","South Asia",38394,0.8,3,71,"H",0,0.80,0.6,1,"W","M","C","H","L",30.0,23.76,3.5,0,0,"H",0,0,7.0,"V","30 GW gross / 23.76 GW techno-econ feasible; state Bitcoin mining precedent (Druk/Bitdeer)"),
("India","South Asia",3287263,1477,3916,39,"M",0,0.90,1.0,0,"S","M","H","M","H",145.3,None,55.1,0.5,0,"H",1,0,0,"V","CEA assessed 145.3 GW (>25MW); Feb 2026 US trade framework incl. GPUs"),
("Pakistan","South Asia",881913,259,408,28,"L",0,0.70,0.6,0,"M","W","H","H","H",60.0,None,10.6,0,0,"E",1,0,0,"V","WAPDA/NEPRA ~60 GW identified; 2 GW allocated to mining/AI DCs 2025"),
("Bangladesh","South Asia",148460,178,458,24,"M",0,0.80,0.3,0,"M","M","H","M","M",0.8,None,0.23,0,0,"H",0,0,0,"V","Kaptai only; Rooppur nuclear building"),
("Sri Lanka","South Asia",65610,23,109,35,"M",0,0.80,0.3,0,"M","M","H","L","M",2.0,1.4,1.4,0,0,"H",1,0,0,"E","Hydro largely developed; Mannar wind"),
("Afghanistan","South Asia",652230,45,20,16,"C",1,0.15,0.2,1,"W","W","M","H","H",23.0,None,0.3,0,0,"E",1,0,0,"P","~23 GW cited (n.v.); crisis state"),
# --- Central Asia & Caucasus ---
("Kazakhstan","Central Asia",2724900,21,303,38,"M",0,0.90,1.0,1,"M","M","M","M","M",5.0,None,3.15,0,0,"M",1,1,0,"E","$10B NVIDIA/Firebird Ekibastuz deal Jun 2026; 300MW->1GW; uranium #1"),
("Uzbekistan","Central Asia",448978,38,147,31,"M",0,0.80,0.6,1,"M","M","M","M","H",8.0,None,2.3,0,0,"H",1,0,0,"E","Mountain hydro program growing; uranium #5"),
("Kyrgyzstan","Central Asia",199951,7.4,22,26,"M",0,0.60,0.6,1,"M","W","M","H","L",36.0,None,4.07,0,0,"M",0,0,0,"E","142 TWh/yr tech, <10%% used (EST-CF045); Kambar-Ata-1 revived; re-export scrutiny"),
("Tajikistan","Central Asia",141376,11,18,19,"M",0,0.70,0.3,1,"W","W","M","H","L",60.0,None,5.89,0,0,"H",0,0,3.0,"E","527 TWh/yr gross, 45%% tech share assumed then EST-CF045; Rogun 3.6 GW ramping"),
("Turkmenistan","Central Asia",488100,7.7,77,17,"M",0,0.50,0.3,1,"W","M","M","M","H",0.5,None,0.01,0,0,"E",0,1,0,"E","Stranded gas reserves; closed economy"),
("Georgia","Central Asia",69700,3.8,38,50,"M",0,0.80,0.6,0,"M","M","C","M","L",15.0,None,3.51,0,0,"M",0,0,1.3,"P","~15 GW tech (n.v.); govt 10 GW by 2032 target; own Black Sea cable"),
("Armenia","Central Asia",29743,2.9,29,46,"M",0,0.90,1.0,1,"M","M","M","H","M",3.0,None,1.37,0,0,"H",0,0,1.0,"V","Firebird AI factory LIVE Aug 2026; 70k+ GPUs/300MW by end-2027 roadmap"),
("Azerbaijan","Central Asia",86600,10.5,76,30,"M",0,0.75,0.6,1,"M","M","M","M","H",3.0,None,1.33,0,0,"M",1,0,1.0,"E","Kura hydro modest; gas exporter"),
# --- East Asia ---
("China","East Asia",9596960,1413,19626,43,"M",1,0.15,1.0,0,"S","S","M","M","M",541.6,400.0,377.0,1.0,0,"M",1,0,0,"V","541.6 GW tech feasible; US export controls bind; domestic chips scaling"),
("Japan","East Asia",377975,122,4435,71,"H",0,1.00,1.0,0,"S","S","M","H","L",26.0,20.0,23.0,23.0,0.61,"L",1,0,0,"V","23 GW geothermal resource (3rd largest), 0.61 installed; consenting-constrained"),
("South Korea","East Asia",100210,52,1872,63,"M",0,1.00,1.0,0,"S","S","M","L","M",2.0,1.2,1.8,0,0,"M",1,0,0,"V","260k+ GPU sovereign program Oct 2025"),
("Taiwan","East Asia",36193,23,920,68,"M",0,1.00,1.0,0,"S","S","M","H","M",5.0,3.0,4.7,0,0,"M",1,0,0,"V","World-class offshore wind; thin reserve margin; cable-cut incidents"),
("Mongolia","East Asia",1564116,3.6,25,31,"M",0,0.75,0.3,1,"W","M","C","M","M",1.0,None,0.03,0,0,"E",1,0,0,"E","Gobi solar/wind exceptional; RU/CN-only fiber transit"),
# --- Southeast Asia & Pacific ---
("Vietnam","SE Asia",331212,102,494,41,"M",0,0.80,0.6,0,"M","M","H","L","M",31.2,24.0,23.1,0,0,"M",1,0,0,"E","123 TWh/yr tech >75%% tapped (EST-CF045); offshore wind south"),
("Laos","SE Asia",236800,8.0,18,34,"M",0,0.70,0.6,1,"M","M","H","L","L",26.0,18.0,9.76,0,0,"M",0,0,33.0,"V","Battery of SE Asia; 26 GW incl Mekong mainstem; ~33 TWh exports; EDL debt distress"),
("Cambodia","SE Asia",181035,18,49,20,"M",0,0.70,0.3,0,"M","M","H","L","L",10.0,None,1.3,0,0,"H",0,0,0,"E","~10 GW cited (n.v.)"),
("Myanmar","SE Asia",676578,55,82,16,"C",1,0.20,0.2,0,"W","W","H","H","L",100.0,46.0,3.3,0,0,"H",0,0,0,"V","WB 108 GW identified / ADB 46 GW at 92 large sites; civil war"),
("Thailand","SE Asia",513120,72,577,33,"M",0,0.85,0.6,0,"S","S","H","L","M",7.0,4.2,4.1,0,0,"H",0,0,0,"E","Mature market"),
("Malaysia","SE Asia",330803,36,472,52,"M",0,0.85,1.0,0,"S","S","H","L","L",12.0,None,6.0,0,0,"M",0,0,0,"E","Johor DC boom; Strategic Trade Permit regime = compliance credibility"),
("Indonesia","SE Asia",1904569,288,1446,34,"M",0,0.85,1.0,0,"S","M","H","H","M",75.0,None,6.57,23.7,2.74,"M",0,0,0,"V","75 GW hydro (ESDM) + 23.7 GW geothermal resource (world #2); Indosat 1 GW program"),
("Philippines","SE Asia",300000,118,487,32,"M",0,0.85,0.6,0,"M","M","H","H","M",13.0,None,5.16,4.5,2.03,"H",1,0,0,"E","~13 GW hydro (n.v.); geothermal world #3"),
("Singapore","SE Asia",728,5.9,604,84,"H",0,1.00,1.0,0,"S","S","H","L","H",0,0,0,0,0,"L",0,0,0,"V","Hub; power-constrained, imports compute-relevant power"),
("Papua New Guinea","SE Asia",462840,11,32,26,"L",0,0.75,0.3,0,"W","W","H","H","L",15.0,9.0,0.3,0,0,"M",0,1,0,"V",">14 GW untapped (IHA); stranded gas/LNG"),
# --- Middle East & North Africa ---
("Saudi Arabia","MENA",2149690,35,1277,57,"M",0,0.85,1.0,0,"S","S","H","L","H",0,0,0,0,0,"E",1,1,0,"V","HUMAIN 6.6 GW by 2034 target; licensed 35k GB300-equiv Nov 2025; behind UAE on framework"),
("UAE","MENA",83600,12,572,69,"H",0,1.00,1.0,0,"S","S","H","L","H",0,0,0,0,0,"E",0,1,0,"V","A:5 status Jul 2026 rule; Stargate UAE 1 GW/~$30B; 5 GW campus; the template"),
("Qatar","MENA",11586,3.2,221,58,"H",0,0.85,1.0,0,"S","S","H","L","H",0,0,0,0,0,"E",0,1,0,"E","Gas surplus"),
("Kuwait","MENA",17818,5.1,158,46,"M",0,0.80,0.6,0,"M","S","H","L","H",0,0,0,0,0,"E",0,1,0,"E",""),
("Oman","MENA",309500,5.7,106,52,"H",0,0.85,0.6,0,"S","S","H","L","H",0,0,0,0,0,"E",1,1,0,"E","Muscat/Salalah cable hub"),
("Israel","MENA",22072,9.6,611,62,"M",0,1.00,1.0,0,"S","S","M","M","H",0,0,0,0,0,"E",0,0,0,"E",""),
("Jordan","MENA",89342,12,62,50,"M",0,0.80,0.6,0,"M","M","M","M","H",0,0,0,0,0,"E",1,0,0,"E",""),
("Turkey","MENA",783562,88,1597,31,"M",0,0.80,0.6,0,"S","S","M","H","H",54.8,40.6,33.0,4.5,1.8,"H",1,0,0,"E","216 TWh tech/160 econ (EST-CF045); geothermal Europe #1"),
("Iraq","MENA",438317,48,264,28,"L",0,0.50,0.3,0,"W","W","H","M","H",4.0,2.5,2.5,0,0,"E",0,1,0,"V","GGFR #3 flaring"),
("Iran","MENA",1648195,93,371,23,"L",2,0.05,0.3,0,"M","W","M","H","H",30.0,None,13.0,0.5,0,"E",0,1,0,"P","Comprehensive sanctions; GGFR #2 flaring"),
("Egypt","MENA",1002450,120,365,30,"M",0,0.80,0.6,0,"S","M","H","L","H",3.7,2.8,2.8,0,0,"E",1,0,0,"V","Suez cable chokepoint hub; El Dabaa nuclear building; Cassava GPU rollout"),
("Algeria","MENA",2381741,48,286,34,"M",0,0.70,0.3,0,"M","M","M","M","H",0.5,None,0.2,0,0,"E",0,1,0,"V","GGFR #7"),
("Libya","MENA",1759540,7.5,45,13,"C",1,0.30,0.2,0,"W","W","H","L","H",0,0,0,0,0,"E",0,1,0,"V","GGFR #6; crisis"),
("Morocco","MENA",446550,39,183,39,"M",0,0.85,0.6,0,"S","M","M","M","H",2.5,1.8,1.8,0,0,"E",1,0,0,"V","Digital Morocco 2030; Atlantic/Med cables; Dakhla solar concepts"),
# --- Sub-Saharan Africa ---
("DR Congo","Africa",2344858,116,93,20,"L",0,0.70,0.3,0,"W","W","H","M","L",100.0,None,2.6,0,0,"M",0,0,0,"V","~100 GW tech feasible (Africa #1); Grand Inga site 40-44 GW; 2.5%% developed; eastern conflict"),
("Ethiopia","Africa",1104300,139,109,38,"L",0,0.75,0.6,1,"W","M","C","M","M",45.0,30.0,10.0,5.0,0.06,"E",1,0,3.0,"V","45 GW potential / 30 econ; GERD fully online; power sold to miners; Addis 2,400m cool"),
("Kenya","Africa",580367,59,136,30,"M",0,0.80,0.6,0,"S","M","M","L","M",3.0,1.8,0.84,10.0,0.98,"H",1,0,0,"V","Geothermal up to 10 GW (world #6 installed); Microsoft/G42 DC stalled on power"),
("Tanzania","Africa",947303,73,87,40,"M",0,0.80,0.6,0,"M","M","H","L","L",4.7,None,2.7,0.65,0,"H",0,1,0,"V","JNHPP 2.1 GW entering service; stranded offshore LNG"),
("Uganda","Africa",241038,53,66,25,"L",0,0.75,0.3,1,"M","M","M","L","L",4.5,None,2.11,0,0,"H",0,0,0.3,"E","Nile sites remain (Ayago); Karuma online"),
("Rwanda","Africa",26338,15,16,58,"M",0,0.80,0.6,1,"M","M","M","L","L",0.5,None,0.1,0,0,"M",0,0,0,"V","Kigali hub ambitions; DRC entanglement"),
("Zambia","Africa",752618,23,29,37,"M",0,0.80,0.3,1,"M","W","M","L","L",6.0,None,3.16,0,0,"E",0,0,0,"P","~6 GW cited (n.v.); drought load-shedding 2024-25"),
("Zimbabwe","Africa",390757,17,53,22,"L",0,0.60,0.3,1,"M","W","M","L","M",4.0,None,1.1,0,0,"E",0,0,0,"E","Batoka Gorge 2.4 GW planned; Harare 1,500m"),
("Mozambique","Africa",801590,37,22,21,"L",0,0.75,0.3,0,"M","M","H","L","L",12.0,None,2.22,0,0,"E",0,1,12.0,"V","12 GW Zambezi; HCB exports to SA; stranded Rovuma LNG"),
("Angola","Africa",1246700,40,142,32,"M",0,0.75,0.3,0,"M","W","H","L","L",18.0,None,3.89,0,0,"E",0,1,0,"V","~18 GW/150 TWh tech; SACS cable to Brazil"),
("Cameroon","Africa",475442,31,59,26,"L",0,0.70,0.3,0,"M","W","H","L","L",23.0,None,1.11,0,0,"M",0,0,0,"V","23 GW/103 TWh tech; Nachtigal online; SAIL cable to Brazil"),
("Nigeria","Africa",923768,242,290,26,"L",0,0.80,0.6,0,"S","W","H","L","M",14.75,None,2.3,0,0,"H",0,1,0,"V","ECN 11.25 large + 3.5 small; GGFR #8; Lagos cable hub; grid collapses"),
("Ghana","Africa",238533,36,115,43,"M",0,0.80,0.6,0,"S","M","H","L","L",2.5,1.6,1.5,0,0,"H",0,0,1.0,"V","Volta developed; 5 cables"),
("Guinea","Africa",245857,15,27,26,"L",0,0.60,0.3,0,"W","W","H","L","L",6.0,None,1.1,0,0,"H",0,0,0,"P","Water tower of W Africa ~6 GW (n.v.); junta"),
("Namibia","Africa",824292,3.2,15,46,"H",0,0.80,0.3,0,"M","M","M","L","M",1.5,None,0.35,0,0,"E",1,1,0,"E","World's highest avg solar (ESMAP); uranium #3; Kudu gas stranded; ~50%% power imported"),
("Botswana","Africa",581730,2.6,20,58,"H",0,0.80,0.3,1,"M","M","M","L","H",0,0,0,0,0,"E",0,0,0,"V","Stable; uranium deposits"),
("South Africa","Africa",1221037,65,427,41,"M",0,0.80,0.6,0,"S","W","M","L","H",3.5,None,3.5,0,0,"E",1,0,0,"V","Eskom fragility; Cassava/NVIDIA first 3,000 GPUs; Koeberg nuclear"),
("Madagascar","Africa",587041,34,20,25,"L",0,0.70,0.3,0,"M","W","M","L","M",45.7,None,0.19,0,0,"E",1,0,0,"E","180 TWh/yr tech <1%% developed (EST-CF045); post-2025 coup"),
("Sudan","Africa",1886068,53,40,14,"C",1,0.20,0.2,0,"W","W","H","L","M",4.5,None,1.6,0,0,"E",1,0,0,"E","Civil war"),
# --- Europe ---
("Norway","Europe",385207,5.7,531,81,"H",0,1.00,1.0,0,"S","S","C","L","L",40.0,36.0,33.9,0,0,"L",1,0,17.0,"V","Stargate Norway Narvik 230MW+; reservoir hydro; DC registration law filters loads"),
("Iceland","Europe",103000,0.4,39,77,"H",0,1.00,1.0,0,"S","S","C","H","L",6.0,3.5,2.29,4.3,0.81,"L",1,0,0,"E","Mature DC industry; power effectively fully allocated; master-plan constrained"),
("Sweden","Europe",450295,11,669,80,"H",0,1.00,1.0,0,"S","S","C","L","L",20.4,18.0,16.4,0,0,"L",1,0,33.0,"V","+4 GW via uprating (AFRY); EcoDataCenter/Mistral lease"),
("Finland","Europe",338424,5.6,317,88,"H",0,1.00,1.0,0,"S","S","C","L","L",3.5,3.2,3.2,0,0,"L",1,0,0,"V","C-Lion1; nuclear OL3"),
("Denmark","Europe",43094,6.0,462,89,"H",0,1.00,1.0,0,"S","S","C","L","L",0,0,0,0,0,"L",1,0,0,"V",""),
("United Kingdom","Europe",243610,70,4003,70,"H",0,1.00,1.0,0,"S","S","C","L","L",3.0,2.4,1.9,0,0,"L",1,0,0,"V","Stargate UK; £150B US package; NE AI Growth Zone to 1.1 GW"),
("Ireland","Europe",70273,5.4,718,76,"H",0,1.00,1.0,0,"S","S","C","L","L",1.0,0.8,0.5,0,0,"L",1,0,0,"V","Dublin new-connection constraints = cautionary incumbent"),
("France","Europe",551695,67,3369,66,"M",0,1.00,1.0,0,"S","S","M","L","M",21.0,20.0,20.0,0,0,"L",1,0,89.0,"V","Nuclear surplus exporter; Mistral buildout; Brookfield €10B"),
("Germany","Europe",357588,84,5048,77,"H",0,1.00,1.0,0,"S","S","M","L","M",14.5,14.0,14.0,0,0,"L",1,0,0,"V","FRA hub; nuclear phased out"),
("Spain","Europe",505990,48,1904,55,"M",0,1.00,1.0,0,"S","S","M","L","H",24.0,23.5,23.0,0,0,"H",1,0,0,"V","Iberian solar + cables"),
("Portugal","Europe",92212,10,346,56,"H",0,1.00,1.0,0,"S","S","M","M","M",8.0,7.5,7.0,0,0,"H",1,0,0,"V","Sines hub"),
("Italy","Europe",301340,59,2550,53,"M",0,1.00,1.0,0,"S","S","M","M","M",25.0,23.0,22.0,2.0,0.92,"H",0,0,0,"V","Larderello geothermal"),
("Greece","Europe",131957,9.9,280,50,"M",0,1.00,0.6,0,"S","S","M","M","H",4.5,3.6,3.4,0,0,"H",1,0,0,"E","Emerging cable hub"),
("Netherlands","Europe",41850,18,1332,78,"H",0,1.00,1.0,0,"S","S","C","L","L",0,0,0,0,0,"L",1,0,0,"V","AMS hub; grid congestion for new large loads"),
("Poland","Europe",312696,38,1036,53,"M",0,1.00,1.0,0,"S","S","M","L","M",2.5,1.8,1.0,0,0,"L",1,0,0,"E","First NPP planned"),
("Czechia","Europe",78871,11,389,59,"H",0,1.00,1.0,1,"S","S","M","L","M",1.5,1.2,1.1,0,0,"L",0,0,0,"E",""),
("Romania","Europe",238397,19,428,45,"M",0,1.00,0.6,0,"M","S","M","M","M",12.0,None,6.6,0,0,"M",1,0,0,"E","Dobrogea wind"),
("Bulgaria","Europe",110879,6.7,131,40,"M",0,1.00,0.6,0,"M","S","M","M","M",4.0,3.0,3.4,0,0,"M",0,0,3.0,"E",""),
("Serbia","Europe",88361,6.6,100,33,"M",0,0.80,0.6,1,"M","M","M","L","L",6.0,None,3.76,0,0,"M",0,0,0,"E","Drina/Morava basins; 2024-26 protests"),
("Albania","Europe",28748,2.8,30,39,"M",0,0.80,0.3,0,"M","M","M","M","L",4.81,None,2.51,0,0,"M",0,0,0,"V","95%%+ hydro generation"),
("Bosnia & Herzegovina","Europe",51197,3.1,33,34,"M",0,0.80,0.3,0,"M","M","M","M","L",6.11,None,2.26,0,0,"M",0,0,0,"V","6.11 GW technical"),
("Ukraine","Europe",603550,40,213,36,"C",0,0.70,0.3,0,"M","W","M","L","M",5.1,4.6,4.7,0,0,"M",1,0,0,"E","War damage ~half of hydro; postwar rebuild upside"),
("Russia","Europe",17098242,143,2588,22,"L",2,0.05,0.3,0,"M","M","C","L","L",582.0,216.0,54.0,0.5,0,"L",1,1,20.0,"E","2,295 TWh gross / 852 econ (EST-CF045); Siberia stranded hydro; comprehensively sanctioned"),
("Switzerland","Europe",41285,9.0,1044,80,"H",0,1.00,1.0,1,"S","S","M","L","L",20.0,19.0,18.0,0,0,"L",0,0,0,"E",""),
("Austria","Europe",83879,9.1,580,69,"H",0,1.00,1.0,1,"S","S","M","L","L",15.0,13.0,11.9,0,0,"L",0,0,0,"E",""),
# --- Americas ---
("United States","Americas",9833517,349,30767,64,"M",0,1.00,1.0,0,"S","S","M","M","M",168.0,115.0,103.0,39.0,3.95,"H",1,1,0,"V","EIA 2024: 103 GW hydro incl PSH; USGS 39 GW conv. geothermal; Permian flaring; the demand center"),
("Canada","Americas",9984670,40,2320,75,"H",0,1.00,1.0,0,"S","S","C","L","L",248.0,None,85.0,0,0,"M",1,0,60.0,"V","163 GW technically feasible remaining (WaterPower Canada); Sovereign AI Compute Strategy; Alberta >10 GW queue"),
("Mexico","Americas",1964375,133,1833,27,"M",0,0.85,1.0,0,"S","M","M","H","H",15.0,13.0,12.6,2.5,0.98,"E",1,1,0,"E","Queretaro DC boom; GGFR #5"),
("Guatemala","Americas",108889,19,121,26,"M",0,0.80,0.3,0,"M","M","M","H","L",6.0,None,1.5,0.3,0.05,"H",0,0,0,"E",""),
("Costa Rica","Americas",51100,5.2,103,56,"H",0,0.85,0.6,0,"M","S","M","H","L",3.5,2.4,2.4,0.5,0.26,"M",1,0,1.0,"E","Renewable grid; Intel/DC presence"),
("Panama","Americas",75417,4.6,90,33,"M",0,0.85,0.6,0,"S","M","H","M","M",3.5,None,1.8,0,0,"M",0,0,0,"E","Regional cable hub"),
("Colombia","Americas",1141748,54,457,37,"M",0,0.85,0.6,0,"S","M","M","H","L",56.0,None,13.0,0,0,"M",1,0,0,"V",">50 GW potential ~22%% used; Hidroituango ramping"),
("Venezuela","Americas",912050,29,100,10,"C",1,0.25,0.2,0,"W","W","H","M","L",30.0,23.0,18.0,0,0,"H",0,1,0,"E","Caroni cascade; Guri 10.2 GW; post-Jan 2026 transition in flux"),
("Ecuador","Americas",256369,18,130,33,"L",0,0.80,0.3,0,"M","W","M","H","L",48.0,39.8,5.19,0,0,"L",0,0,0,"V","189.3 TWh tech / 156.7 econ (EST-CF045), ~7%% tapped; 2024 drought blackouts"),
("Peru","Americas",1285216,35,341,30,"L",0,0.85,0.6,0,"M","M","M","H","M",69.45,None,5.52,2.0,0,"E",1,0,0,"V","69.45 GW, 8%% harnessed; political churn"),
("Bolivia","Americas",1098581,13,64,28,"L",0,0.75,0.3,1,"W","M","C","M","M",40.0,None,0.74,0,0,"E",0,0,0,"V","40 GW tech, 1-2%% used; Altiplano cool + solar; crisis economy"),
("Brazil","Americas",8515767,214,2280,35,"M",0,0.90,1.0,0,"S","S","M","L","L",176.0,None,110.0,0,0,"H",1,0,0,"V","176 GW inventoried, 62%% used; remainder Amazonian; Fortaleza cable hub"),
("Paraguay","Americas",406752,7.1,49,24,"M",0,0.80,0.6,1,"M","M","H","L","L",10.5,9.0,8.81,0,0,"H",0,0,40.0,"V","Itaipu+Yacyreta binational; ~40 TWh exported share = redirectable; ANDE courting AI DCs"),
("Uruguay","Americas",176215,3.4,86,73,"H",0,0.90,0.6,0,"M","S","M","L","L",2.0,1.5,1.5,0,0,"H",1,0,2.0,"V","Top-tier wind share; stable"),
("Argentina","Americas",2780400,46,681,36,"M",0,0.90,0.6,0,"S","M","M","M","M",55.0,None,11.14,0,0,"E",1,1,0,"E","~20%% harnessed (IHA implies ~55 GW); Patagonia wind; Vaca Muerta; Stargate Argentina MoU"),
("Chile","Americas",756102,20,355,63,"M",0,0.90,1.0,0,"S","S","M","H","H",16.0,12.0,7.57,2.0,0.08,"E",1,0,0,"V","Atacama = world-best PV; 2024 National DC Plan; Humboldt cable to Australia"),
("Suriname","Americas",163820,0.6,5,38,"M",0,0.75,0.3,0,"W","M","H","L","L",2.5,None,0.19,0,0,"M",0,0,0,"E",""),
("Guyana","Americas",214969,0.8,27,40,"M",0,0.80,0.3,0,"W","W","H","L","L",7.0,None,0.0,0,0,"M",0,1,0,"E","Amaila revived; gas-to-energy; fastest-growing GDP base"),
# --- Oceania ---
("Australia","Oceania",7692024,27,1840,76,"H",0,1.00,1.0,0,"S","S","M","L","M",12.0,10.0,11.5,0,0,"E",1,0,0,"V","NextDC S7 612MW w/ Stargate; Snowy 2.0; uranium #4"),
("New Zealand","Oceania",268021,5.3,259,81,"H",0,1.00,1.0,0,"S","S","C","H","L",9.0,7.0,5.4,2.7,1.26,"M",1,0,0,"E","Geothermal world #5; consenting-constrained hydro"),
]

# ---- Model constants (v1) ----
VAL_LO, VAL_HI, VAL_C = 60.0, 80.0, 50.0     # $B per GW: ceiling band (Jensen's Math 60-80), central build cost 50
REV_GWYR, CAPTURE = 10.0, 0.20               # $B revenue per GW-yr at GPU-cloud layer; host capture share
SOLAR_GW_PER_KM2 = 0.05                      # 50 MW per km2
SOLAR_LAND_FRAC = 0.001                      # 0.1% of land area convention
SCLASS = {"E":1.0,"H":0.7,"M":0.4,"L":0.15,"0":0.0}
WIND_ADD, GAS_ADD = 10.0, 10.0
F_HYDRO, F_GEO, F_SOLAR, F_WIND, F_GAS, F_EXP = 0.45, 0.85, 0.30, 0.35, 0.85, 0.5
STAB = {"H":1.0,"M":0.65,"L":0.35,"C":0.10}
TRI  = {"S":1.0,"M":0.6,"W":0.25}            # grid
FIB  = {"S":1.0,"M":0.6,"W":0.3}
COOL = {"C":1.0,"M":0.75,"H":0.5}
SEIS = {"L":1.0,"M":0.9,"H":0.8}
WAT  = {"L":1.0,"M":0.925,"H":0.85}
W_GOV,W_STAB,W_GPU,W_GRID,W_FIB,W_MOM,W_PHY,W_CAP = .18,.13,.14,.11,.11,.08,.14,.11

from aux_data import AUX, FD_EST, rating_factor, rating_split, DEM3, DEM_OVERRIDE
from macro_data import M as MACRO, flag as flag_emoji

def model(row):
    (name,region,land,pop,gdp,cpi,stab,sanc,gpu,mom,ll,fib,grid,cool,seis,wat,
     h_tech,h_feas,h_dev,geo_res,geo_dev,sc,wind,gas,exp,flag,note) = row
    if h_feas is None: h_feas = 0.6*h_tech
    solar_ceil = land*SOLAR_LAND_FRAC*SOLAR_GW_PER_KM2*SCLASS[sc]
    ceil_gw = h_tech + geo_res + solar_ceil + wind*WIND_ADD + gas*GAS_ADD
    h_unt = max(h_feas-h_dev, 0.3*(h_tech-h_dev), 0.0)
    g_unt = max(geo_res-geo_dev, 0.0)
    firm = (h_unt*F_HYDRO + g_unt*F_GEO + solar_ceil*F_SOLAR +
            wind*WIND_ADD*F_WIND + gas*GAS_ADD*F_GAS + (exp/8.76)*F_EXP)
    phys = COOL[cool]*SEIS[seis]*WAT[wat]
    eiu_class, eiu_score, rating, fd, msci = AUX[name]
    fd_f = fd if fd is not None else FD_EST[name]
    rat_f = rating_factor(rating)
    capital = 0.5*rat_f + 0.5*fd_f
    real = (W_GOV*cpi/100 + W_STAB*STAB[stab] + W_GPU*gpu + W_GRID*TRI[grid]
            + W_FIB*FIB[fib] + W_MOM*mom + W_PHY*phys + W_CAP*capital)
    cnw_lo, cnw_hi = ceil_gw*VAL_LO, ceil_gw*VAL_HI
    unlock = firm*VAL_C*real
    rev = firm*real*REV_GWYR
    cap = rev*CAPTURE
    ratio = cnw_hi/gdp if gdp else 0
    built = (h_dev + geo_dev) / ceil_gw if ceil_gw > 0 else 0
    iso3, iso2, res_B, resE, ca, caE, debt, m2p = MACRO[name]
    m2_B = round(m2p * gdp / 100)
    unlock_pc = round(unlock * 1000 / pop) if pop else 0        # $ per person (B -> $/person = *1e9/(M*1e6))
    ceiling_pc = round(cnw_hi * 1000 / pop) if pop else 0
    if real < 0.65 and ratio >= 10 and ceil_gw >= 15: tier = "Sleeping Giant"
    elif real >= 0.65 and ratio >= 3: tier = "Primed"
    elif real >= 0.65: tier = "Incumbent"
    elif ratio >= 3: tier = "Emerging Upside"
    else: tier = "Long Road"
    return dict(name=name,region=region,land_km2=land,pop_M=pop,gdp_B=gdp,cpi=cpi,
        stability=stab,sanctions=sanc,gpu_access=gpu,momentum=mom,landlocked=ll,
        fiber=fib,grid=grid,cooling=cool,seismic=seis,water=wat,
        hydro_tech_GW=h_tech,hydro_feas_GW=round(h_feas,1),hydro_dev_GW=h_dev,
        geo_res_GW=geo_res,geo_dev_GW=geo_dev,solar_class=sc,wind_flag=wind,gas_flag=gas,
        export_TWh=exp,solar_ceiling_GW=round(solar_ceil,1),ceiling_GW=round(ceil_gw,1),
        hydro_untapped_GW=round(h_unt,1),firm_GW=round(firm,1),physical=round(phys,3),
        eiu_class=eiu_class,eiu_score=eiu_score,rating=rating,
        dem3=DEM_OVERRIDE.get(name,(DEM3[eiu_class],None))[0],
        dem_note=DEM_OVERRIDE.get(name,(None,None))[1],
        rating_letter=rating_split(rating)[0],rating_agency=rating_split(rating)[1],
        fd_index=round(fd_f,3),
        fd_est=fd is None,msci=msci or "-",capital_access=round(capital,3),
        built_pct=round(built,3),
        iso3=iso3,iso2=iso2,femoji=flag_emoji(iso2),
        reserves_B=res_B,reserves_est=bool(resE),ca_gdp=ca,ca_est=bool(caE),
        debt_gdp=debt,m2_B=m2_B,unlock_pc=unlock_pc,ceiling_pc=ceiling_pc,
        readiness=round(real,3),cnw_ceiling_lo_B=round(cnw_lo),cnw_ceiling_hi_B=round(cnw_hi),
        cnw_unlockable_B=round(unlock),annual_rev_B=round(rev,1),host_capture_B=round(cap,1),
        gdp_multiple=round(ratio,1),tier=tier,flag=flag,note=note)

out = [model(r) for r in R]
with open("cnw_computed.json","w") as f: json.dump(out,f,indent=1)
cols = list(out[0].keys())
with open("cnw_computed.csv","w",newline="") as f:
    w = csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(out)

def show(title, key, n=20, fmt=lambda c: f"{c['cnw_ceiling_hi_B']/1000:7.1f}T ceil | {c['cnw_unlockable_B']:6}B unlock | R={c['readiness']:.2f} | built {c['built_pct']*100:4.1f}% | {c['gdp_multiple']:6.1f}x GDP | {c['tier']}"):
    print(f"\n== {title} ==")
    for c in sorted(out,key=key,reverse=True)[:n]:
        print(f"{c['name']:22s} {fmt(c)}")

if __name__ == "__main__":
    show("TOP 15 BY UNLOCKABLE CNW", lambda c: c['cnw_unlockable_B'], 15)
    show("TOP 15 BY CEILING-TO-GDP MULTIPLE", lambda c: c['gdp_multiple'], 15)
    print("\n== TIER COUNTS ==")
    from collections import Counter
    for t,n in Counter(c['tier'] for c in out).most_common(): print(f"{t}: {n}")
    print(f"\nTotal countries: {len(out)}")
    print("\n== NEPAL DETAIL ==")
    np_ = next(c for c in out if c['name']=='Nepal')
    for k,v in np_.items(): print(f"  {k}: {v}")
    print("\n== TIER FLIPS vs v1 (readiness boundary) ==")
    print("Global ceiling $T:", round(sum(c['cnw_ceiling_hi_B'] for c in out)/1000,1),
          "| unlockable $T:", round(sum(c['cnw_unlockable_B'] for c in out)/1000,1))
    sg = [c for c in out if c['tier']=='Sleeping Giant']
    print("SG count:", len(sg), "| SG ceiling $T:", round(sum(c['cnw_ceiling_hi_B'] for c in sg)/1000,1),
          "| SG GDP $T:", round(sum(c['gdp_B'] for c in sg)/1000,1))
    for nm in ["Bhutan","Madagascar","Namibia","Tajikistan","Mongolia","Paraguay","Kazakhstan","Armenia","UAE","Chile","Colombia","Indonesia","China"]:
        c = next(x for x in out if x['name']==nm)
        print(f"  {nm:14s} R={c['readiness']:.3f} unlock=${c['cnw_unlockable_B']}B {c['gdp_multiple']:.0f}x {c['tier']} | {c['eiu_class']} {c['rating']} FD={c['fd_index']}")
