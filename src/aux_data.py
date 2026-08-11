# Democracy / credit / capital-markets dataset (compiled 2026-08-10)
# EIU Democracy Index 2025 edition (published Feb 2026); ratings best-of S&P/(M)oody's/(F)itch ~mid-2026;
# IMF Financial Development Index (latest published year 2021); MSCI classification 2026 review.
# name: (eiu_class, eiu_score, rating, fd, msci)   fd None -> estimated fallback in model
AUX = {
"Nepal":("Hybrid",4.01,"BB- (F)",0.213,None),
"Bhutan":("Hybrid",5.65,"NR",0.227,None),
"India":("Flawed",6.96,"BBB",0.534,"Emerging"),
"Pakistan":("Authoritarian",2.44,"B-",0.220,"Frontier"),
"Bangladesh":("Hybrid",4.27,"B+",0.243,"Frontier"),
"Sri Lanka":("Flawed",6.57,"CCC+",0.261,"Frontier"),
"Afghanistan":("Authoritarian",0.25,"NR",None,None),
"Kazakhstan":("Authoritarian",2.91,"BBB-",0.354,"Frontier"),
"Uzbekistan":("Authoritarian",2.10,"BB",0.286,None),
"Kyrgyzstan":("Authoritarian",3.27,"B+",0.136,None),
"Tajikistan":("Authoritarian",1.94,"B",0.106,None),
"Turkmenistan":("Authoritarian",1.54,"BB- (F)",0.105,None),
"Georgia":("Hybrid",4.36,"BB",0.333,None),
"Armenia":("Hybrid",5.35,"BB-",0.262,None),
"Azerbaijan":("Authoritarian",2.80,"BB+",0.253,None),
"China":("Authoritarian",2.24,"A+",0.634,"Emerging"),
"Japan":("Full",8.85,"A+",0.888,"Developed"),
"South Korea":("Flawed",7.75,"AA",0.818,"Emerging"),
"Taiwan":("Full",8.78,"AA+",None,"Emerging"),
"Mongolia":("Flawed",6.50,"BB-",0.308,None),
"Vietnam":("Authoritarian",2.62,"BB+",0.382,"Frontier"),
"Laos":("Authoritarian",1.71,"CCC+",0.170,None),
"Cambodia":("Authoritarian",2.70,"B (M)",0.210,None),
"Myanmar":("Authoritarian",0.96,"NR",0.126,None),
"Thailand":("Flawed",6.59,"BBB+",0.731,"Emerging"),
"Malaysia":("Flawed",7.11,"A-",0.727,"Emerging"),
"Indonesia":("Flawed",6.37,"BBB",0.364,"Emerging"),
"Philippines":("Flawed",6.31,"BBB+",0.379,"Emerging"),
"Singapore":("Flawed",6.18,"AAA",0.704,"Developed"),
"Papua New Guinea":("Hybrid",5.90,"B-",0.184,None),
"Saudi Arabia":("Authoritarian",2.08,"A+",0.442,"Emerging"),
"UAE":("Authoritarian",3.18,"AA",0.486,"Emerging"),
"Qatar":("Authoritarian",3.17,"AA",0.530,"Emerging"),
"Kuwait":("Authoritarian",2.78,"AA-",0.400,"Emerging"),
"Oman":("Authoritarian",3.05,"BBB-",0.384,"Frontier"),
"Israel":("Flawed",7.80,"A",0.605,"Developed"),
"Jordan":("Authoritarian",3.28,"BB-",0.359,"Frontier"),
"Turkey":("Hybrid",4.26,"BB-",0.500,"Emerging"),
"Iraq":("Authoritarian",3.13,"B-",None,None),
"Iran":("Authoritarian",1.96,"NR",0.522,None),
"DR Congo":("Authoritarian",1.92,"B-",0.066,None),
"Ethiopia":("Authoritarian",3.13,"SD",0.116,None),
"Kenya":("Hybrid",5.05,"B",0.165,"Frontier"),
"Tanzania":("Hybrid",5.13,"B+ (F)",0.103,None),
"Uganda":("Hybrid",4.31,"B-",0.104,None),
"Rwanda":("Authoritarian",3.34,"B+",0.159,None),
"Zambia":("Hybrid",5.82,"CCC+",0.199,None),
"Zimbabwe":("Authoritarian",2.98,"NR",None,"Standalone"),
"Mozambique":("Authoritarian",3.38,"CCC+",0.155,None),
"Angola":("Authoritarian",3.94,"B-",0.139,None),
"Cameroon":("Authoritarian",2.56,"B-",0.101,None),
"Nigeria":("Hybrid",4.10,"B-",0.221,"Standalone"),
"Ghana":("Flawed",6.24,"B-",0.178,None),
"Guinea":("Authoritarian",2.15,"B+",0.107,None),
"Morocco":("Hybrid",4.97,"BBB-",0.351,"Frontier"),
"Egypt":("Authoritarian",2.79,"B",0.309,"Emerging"),
"Algeria":("Authoritarian",3.55,"NR",0.141,None),
"Libya":("Authoritarian",2.31,"NR",0.128,None),
"Namibia":("Flawed",6.48,"BB- (F)",0.402,None),
"Botswana":("Flawed",7.63,"BBB",0.345,"Standalone"),
"South Africa":("Flawed",7.16,"BB",0.546,"Emerging"),
"Madagascar":("Hybrid",5.06,"B-",0.106,None),
"Sudan":("Authoritarian",1.46,"NR",0.108,None),
"Norway":("Full",9.81,"AAA",0.636,"Developed"),
"Iceland":("Full",9.38,"A+",0.496,"Frontier"),
"Sweden":("Full",9.35,"AAA",0.775,"Developed"),
"Finland":("Full",9.37,"AA+",0.646,"Developed"),
"Denmark":("Full",9.42,"AAA",0.665,"Developed"),
"United Kingdom":("Full",8.34,"AA",0.836,"Developed"),
"Ireland":("Full",9.33,"AA+",0.625,"Developed"),
"France":("Full",8.05,"A+",0.815,"Developed"),
"Germany":("Full",8.73,"AAA",0.702,"Developed"),
"Spain":("Full",8.20,"A+",0.803,"Developed"),
"Portugal":("Full",8.28,"A+",0.654,"Developed"),
"Italy":("Flawed",7.58,"BBB+",0.767,"Developed"),
"Greece":("Full",8.07,"BBB",0.474,"Emerging"),
"Netherlands":("Full",8.93,"AAA",0.709,"Developed"),
"Poland":("Flawed",7.65,"A-",0.431,"Emerging"),
"Czechia":("Full",8.15,"AA-",0.317,"Emerging"),
"Romania":("Flawed",6.11,"BBB-",0.275,"Frontier"),
"Bulgaria":("Flawed",6.34,"BBB+",0.379,"Standalone"),
"Serbia":("Flawed",6.30,"BBB-",0.256,"Frontier"),
"Albania":("Flawed",6.20,"BB",0.203,None),
"Bosnia & Herzegovina":("Hybrid",5.23,"B+",0.266,"Standalone"),
"Ukraine":("Hybrid",4.79,"CCC+",0.207,"Standalone"),
"Russia":("Authoritarian",2.03,"NR",0.530,"Standalone"),
"Switzerland":("Full",9.32,"AAA",0.939,"Developed"),
"Austria":("Full",8.42,"AA+",0.658,"Developed"),
"United States":("Flawed",7.65,"AA+",0.917,"Developed"),
"Canada":("Full",9.08,"AAA",0.874,"Developed"),
"Mexico":("Hybrid",5.40,"BBB",0.402,"Emerging"),
"Guatemala":("Hybrid",4.65,"BB+",0.216,None),
"Costa Rica":("Full",8.29,"BB",0.288,None),
"Panama":("Flawed",7.04,"BBB-",0.465,"Standalone"),
"Colombia":("Flawed",6.04,"BB",0.388,"Emerging"),
"Venezuela":("Authoritarian",2.13,"NR",0.239,None),
"Ecuador":("Hybrid",5.20,"B-",0.170,None),
"Peru":("Hybrid",5.88,"BBB-",0.374,"Emerging"),
"Bolivia":("Hybrid",5.38,"CCC+",0.392,None),
"Brazil":("Flawed",6.76,"BB",0.662,"Emerging"),
"Paraguay":("Flawed",6.04,"BBB-",0.193,None),
"Uruguay":("Full",8.92,"BBB+",0.304,None),
"Argentina":("Flawed",6.89,"CCC+",0.306,"Standalone"),
"Chile":("Flawed",7.97,"A",0.504,"Emerging"),
"Suriname":("Flawed",7.03,"CCC+",0.183,None),
"Guyana":("Flawed",6.09,"NR",0.147,None),
"Australia":("Full",8.85,"AAA",0.909,"Developed"),
"New Zealand":("Full",9.62,"AA+",0.617,"Developed"),
}
# FD estimated fallbacks where IMF index has no entry (flagged E)
FD_EST = {"Afghanistan":0.05,"Taiwan":0.70,"Iraq":0.10,"Zimbabwe":0.10}
# rating letter -> capital-access factor
def rating_factor(r):
    r0 = r.replace(" (F)","").replace(" (M)","").strip()
    if r0 == "NR": return 0.28
    if r0 in ("SD","RD"): return 0.10
    base = r0.rstrip("+-")
    return {"AAA":1.0,"AA":0.95,"A":0.85,"BBB":0.72,"BB":0.55,"B":0.40,"CCC":0.18,"CC":0.15,"C":0.15}.get(base,0.28)

# rating string -> (letter, agency name). No suffix = S&P (the dataset's preferred agency).
def rating_split(r):
    if r.endswith(" (F)"): return r[:-4], "Fitch"
    if r.endswith(" (M)"): return r[:-4], "Moody's"
    if r == "NR": return "NR", "unrated"
    return r, "S&P"

# EIU class -> three-bucket display: Democracy (Full+Flawed) / Hybrid / Authoritarian
DEM3 = {"Full":"Democracy","Flawed":"Democracy","Hybrid":"Hybrid","Authoritarian":"Authoritarian"}
# Post-EIU-cutoff election adjustment: applied where the EIU 2025 score was taken under a
# transitional/unelected government that a subsequent competitive election with peaceful
# transfer has since replaced. Sole qualifying case as of Aug 2026:
DEM_OVERRIDE = {"Nepal": ("Democracy",
    "EIU 2025 (4.01) scored Nepal mid-transition under the interim government; the March 2026 "
    "election produced a competitive landslide and peaceful transfer to an elected majority "
    "government. Classified Democracy on post-election basis.")}
