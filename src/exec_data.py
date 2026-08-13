# Execution-capacity inputs (compiled 2026-08-11, knowledge-based estimates, E-flagged throughout)
# iso3: (installed_grid_GW, us_hyperscaler_cloud_regions)
# Cloud regions = count of AWS / Microsoft Azure / Google Cloud with an operational full region
# in-country (announced-only not counted; borderline cases rounded down). A cloud region is a hard
# execution signal: it certifies land, power, permitting, connectivity, and US export comfort at once.
EXEC = {
"USA":(1300,3),"CHN":(3350,2),"IND":(470,3),"JPN":(340,3),"RUS":(250,0),"DEU":(270,3),"BRA":(230,3),
"CAN":(155,3),"FRA":(145,3),"KOR":(145,3),"GBR":(110,3),"ITA":(130,3),"ESP":(130,3),"TUR":(115,0),
"AUS":(100,3),"MEX":(90,3),"SAU":(90,2),"IDN":(90,3),"IRN":(90,0),"VNM":(85,0),"TWN":(65,2),
"POL":(65,2),"ZAF":(63,3),"EGY":(60,0),"THA":(55,1),"UKR":(35,0),"ARG":(45,0),"PAK":(46,0),
"NLD":(45,2),"SWE":(45,2),"ARE":(45,3),"MYS":(40,3),"NOR":(40,1),"CHE":(22,3),"CHL":(35,2),
"IRQ":(35,0),"VEN":(12,0),"PHL":(30,1),"BGD":(30,0),"FIN":(25,1),"AUT":(27,0),"KAZ":(24,0),
"DZA":(25,0),"CZE":(21,0),"GRC":(22,0),"PRT":(22,0),"ISR":(21,3),"ROU":(20,0),"KWT":(20,1),
"DNK":(20,0),"COL":(20,0),"UZB":(17,0),"PER":(16,0),"NGA":(13,0),"SGP":(12,3),"LAO":(12,0),
"IRL":(12,3),"MAR":(12,0),"BGR":(12,0),"QAT":(11,2),"LBY":(10,0),"OMN":(10,0),
"NZL":(10,2),"AZE":(8,0),"PRY":(8.8,0),"ECU":(8.8,0),"SRB":(8.5,0),"JOR":(7,0),"TKM":(7,0),
"MMR":(7,0),"TJK":(6.5,0),"AGO":(6.2,0),"ETH":(6,0),"GHA":(5.5,0),"GTM":(5.3,0),"LKA":(5,0),
"URY":(5,0),"BIH":(4.5,0),"PAN":(4.5,0),"GEO":(4.6,0),"KGZ":(4,0),"KHM":(4,0),"KEN":(3.8,0),
"ZMB":(3.8,0),"BOL":(3.7,0),"CRI":(3.7,0),"NPL":(3.5,0),"ARM":(3.5,0),"SDN":(3.5,0),"ISL":(3,0),
"COD":(2.9,0),"MOZ":(2.9,0),"ALB":(2.6,0),"ZWE":(2.5,0),"BTN":(2.4,0),"TZA":(2.2,0),"UGA":(2.05,0),
"CMR":(1.7,0),"MNG":(1.6,0),"PNG":(1.2,0),"GIN":(1,0),"BWA":(1,0),"MDG":(0.9,0),"NAM":(0.7,0),
"AFG":(0.7,0),"SUR":(0.6,0),"GUY":(0.4,0),"RWA":(0.3,0),
}
OECD = {"USA","CAN","MEX","GBR","IRL","FRA","DEU","ESP","PRT","ITA","GRC","NLD","POL","CZE","AUT",
"CHE","SWE","NOR","FIN","DNK","TUR","ISR","JPN","KOR","AUS","NZL","CHL","COL","CRI"}
# achievable PUE band from cooling class (climate-driven; per-country *average* PUE has no public series)
PUE_BAND = {"C": "~1.1-1.25", "M": "~1.2-1.4", "H": "~1.35-1.6"}
