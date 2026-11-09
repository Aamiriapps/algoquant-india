import os
import csv
import json
import time
import urllib.request
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
UNIVERSE_CACHE_FILE = os.path.join(CACHE_DIR, "dynamic_universe.json")
NSE_NIFTY500_URL = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"

# Master database of official NSE Nifty 500 companies
MASTER_NSE_UNIVERSE = [
    {"symbol": "360ONE", "name": "360 ONE WAM Ltd.", "sector": "Financial Services"},
    {"symbol": "ABB", "name": "ABB India Ltd.", "sector": "Capital Goods"},
    {"symbol": "ACC", "name": "ACC Ltd.", "sector": "Construction Materials"},
    {"symbol": "ACMESOLAR", "name": "ACME Solar Holdings Ltd.", "sector": "Power"},
    {"symbol": "AIAENG", "name": "AIA Engineering Ltd.", "sector": "Capital Goods"},
    {"symbol": "APLAPOLLO", "name": "APL Apollo Tubes Ltd.", "sector": "Capital Goods"},
    {"symbol": "AUBANK", "name": "AU Small Finance Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "AWL", "name": "AWL Agri Business Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "AADHARHFC", "name": "Aadhar Housing Finance Ltd.", "sector": "Financial Services"},
    {"symbol": "AARTIIND", "name": "Aarti Industries Ltd.", "sector": "Chemicals"},
    {"symbol": "AAVAS", "name": "Aavas Financiers Ltd.", "sector": "Financial Services"},
    {"symbol": "ABBOTINDIA", "name": "Abbott India Ltd.", "sector": "Healthcare"},
    {"symbol": "ACE", "name": "Action Construction Equipment Ltd.", "sector": "Capital Goods"},
    {"symbol": "ACUTAAS", "name": "Acutaas Chemicals Ltd.", "sector": "Healthcare"},
    {"symbol": "ADANIENSOL", "name": "Adani Energy Solutions Ltd.", "sector": "Power"},
    {"symbol": "ADANIENT", "name": "Adani Enterprises Ltd.", "sector": "Metals & Mining"},
    {"symbol": "ADANIGREEN", "name": "Adani Green Energy Ltd.", "sector": "Power"},
    {"symbol": "ADANIPORTS", "name": "Adani Ports and Special Economic Zone Ltd.", "sector": "Services"},
    {"symbol": "ADANIPOWER", "name": "Adani Power Ltd.", "sector": "Power"},
    {"symbol": "ATGL", "name": "Adani Total Gas Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "ABCAPITAL", "name": "Aditya Birla Capital Ltd.", "sector": "Financial Services"},
    {"symbol": "ABREL", "name": "Aditya Birla Real Estate Ltd.", "sector": "Realty"},
    {"symbol": "ABSLAMC", "name": "Aditya Birla Sun Life AMC Ltd.", "sector": "Financial Services"},
    {"symbol": "CPPLUS", "name": "Aditya Infotech Ltd.", "sector": "Capital Goods"},
    {"symbol": "AEGISLOG", "name": "Aegis Logistics Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "AEGISVOPAK", "name": "Aegis Vopak Terminals Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "AETHER", "name": "Aether Industries Ltd.", "sector": "Chemicals"},
    {"symbol": "AFCONS", "name": "Afcons Infrastructure Ltd.", "sector": "Construction"},
    {"symbol": "AFFLE", "name": "Affle 3i Ltd.", "sector": "Information Technology"},
    {"symbol": "AJANTPHARM", "name": "Ajanta Pharmaceuticals Ltd.", "sector": "Healthcare"},
    {"symbol": "ALKEM", "name": "Alkem Laboratories Ltd.", "sector": "Healthcare"},
    {"symbol": "ABDL", "name": "Allied Blenders and Distillers Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "ARE&M", "name": "Amara Raja Energy & Mobility Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "AMBER", "name": "Amber Enterprises India Ltd.", "sector": "Consumer Durables"},
    {"symbol": "AMBUJACEM", "name": "Ambuja Cements Ltd.", "sector": "Construction Materials"},
    {"symbol": "ANANDRATHI", "name": "Anand Rathi Wealth Ltd.", "sector": "Financial Services"},
    {"symbol": "ANANTRAJ", "name": "Anant Raj Ltd.", "sector": "Realty"},
    {"symbol": "ANGELONE", "name": "Angel One Ltd.", "sector": "Financial Services"},
    {"symbol": "ANTHEM", "name": "Anthem Biosciences Ltd.", "sector": "Healthcare"},
    {"symbol": "ANURAS", "name": "Anupam Rasayan India Ltd.", "sector": "Chemicals"},
    {"symbol": "APARINDS", "name": "Apar Industries Ltd.", "sector": "Capital Goods"},
    {"symbol": "APOLLOHOSP", "name": "Apollo Hospitals Enterprise Ltd.", "sector": "Healthcare"},
    {"symbol": "APOLLOTYRE", "name": "Apollo Tyres Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "APTUS", "name": "Aptus Value Housing Finance India Ltd.", "sector": "Financial Services"},
    {"symbol": "ASAHIINDIA", "name": "Asahi India Glass Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "ASHOKLEY", "name": "Ashok Leyland Ltd.", "sector": "Capital Goods"},
    {"symbol": "ASIANPAINT", "name": "Asian Paints Ltd.", "sector": "Consumer Durables"},
    {"symbol": "ASTERDM", "name": "Aster DM Quality Care Ltd.", "sector": "Healthcare"},
    {"symbol": "ASTRAL", "name": "Astral Ltd.", "sector": "Capital Goods"},
    {"symbol": "ATHERENERG", "name": "Ather Energy Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "ATUL", "name": "Atul Ltd.", "sector": "Chemicals"},
    {"symbol": "AUROPHARMA", "name": "Aurobindo Pharma Ltd.", "sector": "Healthcare"},
    {"symbol": "AIIL", "name": "Authum Investment & Infrastructure Ltd.", "sector": "Financial Services"},
    {"symbol": "AVANTIFEED", "name": "Avanti Feeds Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "DMART", "name": "Avenue Supermarts Ltd.", "sector": "Consumer Services"},
    {"symbol": "AXISBANK", "name": "Axis Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "AZAD", "name": "Azad Engineering Ltd.", "sector": "Capital Goods"},
    {"symbol": "BEML", "name": "BEML Ltd.", "sector": "Capital Goods"},
    {"symbol": "BLS", "name": "BLS International Services Ltd.", "sector": "Consumer Services"},
    {"symbol": "BSE", "name": "BSE Ltd.", "sector": "Financial Services"},
    {"symbol": "BAJAJ-AUTO", "name": "Bajaj Auto Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd.", "sector": "Financial Services"},
    {"symbol": "BAJAJFINSV", "name": "Bajaj Finserv Ltd.", "sector": "Financial Services"},
    {"symbol": "BAJAJHLDNG", "name": "Bajaj Holdings & Investment Ltd.", "sector": "Financial Services"},
    {"symbol": "BAJAJHFL", "name": "Bajaj Housing Finance Ltd.", "sector": "Financial Services"},
    {"symbol": "BALKRISIND", "name": "Balkrishna Industries Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "BALRAMCHIN", "name": "Balrampur Chini Mills Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "BANDHANBNK", "name": "Bandhan Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "BANKBARODA", "name": "Bank of Baroda", "sector": "Financial Services"},
    {"symbol": "BANKINDIA", "name": "Bank of India", "sector": "Financial Services"},
    {"symbol": "MAHABANK", "name": "Bank of Maharashtra", "sector": "Financial Services"},
    {"symbol": "BATAINDIA", "name": "Bata India Ltd.", "sector": "Consumer Durables"},
    {"symbol": "BELRISE", "name": "Belrise Industries Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "BERGEPAINT", "name": "Berger Paints India Ltd.", "sector": "Consumer Durables"},
    {"symbol": "BHARATCOAL", "name": "Bharat Coking Coal Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "BDL", "name": "Bharat Dynamics Ltd.", "sector": "Capital Goods"},
    {"symbol": "BEL", "name": "Bharat Electronics Ltd.", "sector": "Capital Goods"},
    {"symbol": "BHARATFORG", "name": "Bharat Forge Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "BHEL", "name": "Bharat Heavy Electricals Ltd.", "sector": "Capital Goods"},
    {"symbol": "BPCL", "name": "Bharat Petroleum Corporation Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd.", "sector": "Telecommunication"},
    {"symbol": "BHARTIHEXA", "name": "Bharti Hexacom Ltd.", "sector": "Telecommunication"},
    {"symbol": "GROWW", "name": "Billionbrains Garage Ventures Ltd.", "sector": "Financial Services"},
    {"symbol": "BIOCON", "name": "Biocon Ltd.", "sector": "Healthcare"},
    {"symbol": "BSOFT", "name": "Birlasoft Ltd.", "sector": "Information Technology"},
    {"symbol": "BBOX", "name": "Black Box Ltd.", "sector": "Information Technology"},
    {"symbol": "BLUESTARCO", "name": "Blue Star Ltd.", "sector": "Consumer Durables"},
    {"symbol": "BOSCHLTD", "name": "Bosch Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "FIRSTCRY", "name": "Brainbees Solutions Ltd.", "sector": "Consumer Services"},
    {"symbol": "BRIGADE", "name": "Brigade Enterprises Ltd.", "sector": "Realty"},
    {"symbol": "BRITANNIA", "name": "Britannia Industries Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "BIRET", "name": "Brookfield India Real Estate Trust", "sector": "Realty"},
    {"symbol": "CCL", "name": "CCL Products (I) Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "CESC", "name": "CESC Ltd.", "sector": "Power"},
    {"symbol": "CGPOWER", "name": "CG Power and Industrial Solutions Ltd.", "sector": "Capital Goods"},
    {"symbol": "CIEINDIA", "name": "CIE Automotive India Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "CRISIL", "name": "CRISIL Ltd.", "sector": "Financial Services"},
    {"symbol": "CANFINHOME", "name": "Can Fin Homes Ltd.", "sector": "Financial Services"},
    {"symbol": "CANBK", "name": "Canara Bank", "sector": "Financial Services"},
    {"symbol": "CANHLIFE", "name": "Canara HSBC Life Insurance Company Ltd.", "sector": "Financial Services"},
    {"symbol": "CAPLIPOINT", "name": "Caplin Point Laboratories Ltd.", "sector": "Healthcare"},
    {"symbol": "CGCL", "name": "Capri Global Capital Ltd.", "sector": "Financial Services"},
    {"symbol": "CARBORUNIV", "name": "Carborundum Universal Ltd.", "sector": "Capital Goods"},
    {"symbol": "CARTRADE", "name": "Cartrade Tech Ltd.", "sector": "Consumer Services"},
    {"symbol": "CASTROLIND", "name": "Castrol India Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "CEATLTD", "name": "Ceat Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "CEMPRO", "name": "Cemindia Projects Ltd.", "sector": "Construction"},
    {"symbol": "CENTRALBK", "name": "Central Bank of India", "sector": "Financial Services"},
    {"symbol": "CDSL", "name": "Central Depository Services (India) Ltd.", "sector": "Financial Services"},
    {"symbol": "CMPDI", "name": "Central Mine Planning & Design Institute Ltd.", "sector": "Services"},
    {"symbol": "CHAMBLFERT", "name": "Chambal Fertilizers & Chemicals Ltd.", "sector": "Chemicals"},
    {"symbol": "CHENNPETRO", "name": "Chennai Petroleum Corporation Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "CHOICEIN", "name": "Choice International Ltd.", "sector": "Financial Services"},
    {"symbol": "CHOLAHLDNG", "name": "Cholamandalam Financial Holdings Ltd.", "sector": "Financial Services"},
    {"symbol": "CHOLAFIN", "name": "Cholamandalam Investment and Finance Company Ltd.", "sector": "Financial Services"},
    {"symbol": "CIPLA", "name": "Cipla Ltd.", "sector": "Healthcare"},
    {"symbol": "CUB", "name": "City Union Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "CLEANMAX", "name": "Clean Max Enviro Energy Solutions Ltd.", "sector": "Power"},
    {"symbol": "CLEAN", "name": "Clean Science and Technology Ltd.", "sector": "Chemicals"},
    {"symbol": "COALINDIA", "name": "Coal India Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "COCHINSHIP", "name": "Cochin Shipyard Ltd.", "sector": "Capital Goods"},
    {"symbol": "COFORGE", "name": "Coforge Ltd.", "sector": "Information Technology"},
    {"symbol": "COHANCE", "name": "Cohance Lifesciences Ltd.", "sector": "Healthcare"},
    {"symbol": "COLPAL", "name": "Colgate Palmolive (India) Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "CAMS", "name": "Computer Age Management Services Ltd.", "sector": "Financial Services"},
    {"symbol": "CONCORDBIO", "name": "Concord Biotech Ltd.", "sector": "Healthcare"},
    {"symbol": "CONCOR", "name": "Container Corporation of India Ltd.", "sector": "Services"},
    {"symbol": "COROMANDEL", "name": "Coromandel International Ltd.", "sector": "Chemicals"},
    {"symbol": "CORONA", "name": "Corona Remedies Ltd.", "sector": "Healthcare"},
    {"symbol": "CRAFTSMAN", "name": "Craftsman Automation Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "CREDITACC", "name": "CreditAccess Grameen Ltd.", "sector": "Financial Services"},
    {"symbol": "CROMPTON", "name": "Crompton Greaves Consumer Electricals Ltd.", "sector": "Consumer Durables"},
    {"symbol": "CUMMINSIND", "name": "Cummins India Ltd.", "sector": "Capital Goods"},
    {"symbol": "CUPID", "name": "Cupid Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "CYIENT", "name": "Cyient Ltd.", "sector": "Information Technology"},
    {"symbol": "DLF", "name": "DLF Ltd.", "sector": "Realty"},
    {"symbol": "DOMS", "name": "DOMS Industries Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "DABUR", "name": "Dabur India Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "DALBHARAT", "name": "Dalmia Bharat Ltd.", "sector": "Construction Materials"},
    {"symbol": "DATAPATTNS", "name": "Data Patterns (India) Ltd.", "sector": "Capital Goods"},
    {"symbol": "DEEPAKFERT", "name": "Deepak Fertilisers & Petrochemicals Corp. Ltd.", "sector": "Chemicals"},
    {"symbol": "DEEPAKNTR", "name": "Deepak Nitrite Ltd.", "sector": "Chemicals"},
    {"symbol": "DELHIVERY", "name": "Delhivery Ltd.", "sector": "Services"},
    {"symbol": "DEVYANI", "name": "Devyani International Ltd.", "sector": "Consumer Services"},
    {"symbol": "DIVISLAB", "name": "Divi's Laboratories Ltd.", "sector": "Healthcare"},
    {"symbol": "DIXON", "name": "Dixon Technologies (India) Ltd.", "sector": "Consumer Durables"},
    {"symbol": "LALPATHLAB", "name": "Dr. Lal Path Labs Ltd.", "sector": "Healthcare"},
    {"symbol": "DRREDDY", "name": "Dr. Reddy's Laboratories Ltd.", "sector": "Healthcare"},
    {"symbol": "HEG", "name": "HEG Ltd.", "sector": "Capital Goods"},
    {"symbol": "EIDPARRY", "name": "E.I.D. Parry (India) Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "EIHOTEL", "name": "EIH Ltd.", "sector": "Consumer Services"},
    {"symbol": "EMBASSY", "name": "EMBASSY OFFICE PARKS REIT", "sector": "Realty"},
    {"symbol": "EICHERMOT", "name": "Eicher Motors Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "ELECON", "name": "Elecon Engineering Co. Ltd.", "sector": "Capital Goods"},
    {"symbol": "ELGIEQUIP", "name": "Elgi Equipments Ltd.", "sector": "Capital Goods"},
    {"symbol": "EMAMILTD", "name": "Emami Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "EMCURE", "name": "Emcure Pharmaceuticals Ltd.", "sector": "Healthcare"},
    {"symbol": "EMMVEE", "name": "Emmvee Photovoltaic Power Ltd.", "sector": "Capital Goods"},
    {"symbol": "ENDURANCE", "name": "Endurance Technologies Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "ENGINERSIN", "name": "Engineers India Ltd.", "sector": "Construction"},
    {"symbol": "ESCORTS", "name": "Escorts Kubota Ltd.", "sector": "Capital Goods"},
    {"symbol": "ETERNAL", "name": "Eternal Ltd.", "sector": "Consumer Services"},
    {"symbol": "EXIDEIND", "name": "Exide Industries Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "NYKAA", "name": "FSN E-Commerce Ventures Ltd.", "sector": "Consumer Services"},
    {"symbol": "FEDERALBNK", "name": "Federal Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "FACT", "name": "Fertilisers and Chemicals Travancore Ltd.", "sector": "Chemicals"},
    {"symbol": "FINCABLES", "name": "Finolex Cables Ltd.", "sector": "Capital Goods"},
    {"symbol": "FSL", "name": "Firstsource Solutions Ltd.", "sector": "Services"},
    {"symbol": "FIVESTAR", "name": "Five-Star Business Finance Ltd.", "sector": "Financial Services"},
    {"symbol": "FORCEMOT", "name": "Force Motors Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "FORTIS", "name": "Fortis Healthcare Ltd.", "sector": "Healthcare"},
    {"symbol": "FRACTAL", "name": "Fractal Analytics Ltd.", "sector": "Information Technology"},
    {"symbol": "GAIL", "name": "GAIL (India) Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "GVT&D", "name": "GE Vernova T&D India Ltd.", "sector": "Capital Goods"},
    {"symbol": "GMRAIRPORT", "name": "GMR Airports Ltd.", "sector": "Services"},
    {"symbol": "GABRIEL", "name": "Gabriel India Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "GALLANTT", "name": "Gallantt Ispat Ltd.", "sector": "Capital Goods"},
    {"symbol": "GRSE", "name": "Garden Reach Shipbuilders & Engineers Ltd.", "sector": "Capital Goods"},
    {"symbol": "GICRE", "name": "General Insurance Corporation of India", "sector": "Financial Services"},
    {"symbol": "GILLETTE", "name": "Gillette India Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "GLAND", "name": "Gland Pharma Ltd.", "sector": "Healthcare"},
    {"symbol": "GLAXO", "name": "Glaxosmithkline Pharmaceuticals Ltd.", "sector": "Healthcare"},
    {"symbol": "GLENMARK", "name": "Glenmark Pharmaceuticals Ltd.", "sector": "Healthcare"},
    {"symbol": "MEDANTA", "name": "Global Health Ltd.", "sector": "Healthcare"},
    {"symbol": "GPIL", "name": "Godawari Power & Ispat Ltd.", "sector": "Capital Goods"},
    {"symbol": "GODFRYPHLP", "name": "Godfrey Phillips India Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "GODREJCP", "name": "Godrej Consumer Products Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "GODREJIND", "name": "Godrej Industries Ltd.", "sector": "Diversified"},
    {"symbol": "GODREJPROP", "name": "Godrej Properties Ltd.", "sector": "Realty"},
    {"symbol": "GRANULES", "name": "Granules India Ltd.", "sector": "Healthcare"},
    {"symbol": "GRAPHITE", "name": "Graphite India Ltd.", "sector": "Capital Goods"},
    {"symbol": "GRASIM", "name": "Grasim Industries Ltd.", "sector": "Construction Materials"},
    {"symbol": "GRAVITA", "name": "Gravita India Ltd.", "sector": "Metals & Mining"},
    {"symbol": "GESHIP", "name": "Great Eastern Shipping Co. Ltd.", "sector": "Services"},
    {"symbol": "FLUOROCHEM", "name": "Gujarat Fluorochemicals Ltd.", "sector": "Chemicals"},
    {"symbol": "GMDCLTD", "name": "Gujarat Mineral Development Corporation Ltd.", "sector": "Metals & Mining"},
    {"symbol": "HBLENGINE", "name": "HBL Engineering Ltd.", "sector": "Capital Goods"},
    {"symbol": "HCLTECH", "name": "HCL Technologies Ltd.", "sector": "Information Technology"},
    {"symbol": "HDBFS", "name": "HDB Financial Services Ltd.", "sector": "Financial Services"},
    {"symbol": "HDFCAMC", "name": "HDFC Asset Management Company Ltd.", "sector": "Financial Services"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "HDFCLIFE", "name": "HDFC Life Insurance Company Ltd.", "sector": "Financial Services"},
    {"symbol": "HEGAM", "name": "HEG Advanced Materials Ltd.", "sector": "Capital Goods"},
    {"symbol": "HFCL", "name": "HFCL Ltd.", "sector": "Telecommunication"},
    {"symbol": "HAVELLS", "name": "Havells India Ltd.", "sector": "Consumer Durables"},
    {"symbol": "HEROMOTOCO", "name": "Hero MotoCorp Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "HEXT", "name": "Hexaware Technologies Ltd.", "sector": "Information Technology"},
    {"symbol": "HSCL", "name": "Himadri Speciality Chemical Ltd.", "sector": "Chemicals"},
    {"symbol": "HINDALCO", "name": "Hindalco Industries Ltd.", "sector": "Metals & Mining"},
    {"symbol": "HAL", "name": "Hindustan Aeronautics Ltd.", "sector": "Capital Goods"},
    {"symbol": "HINDCOPPER", "name": "Hindustan Copper Ltd.", "sector": "Metals & Mining"},
    {"symbol": "HINDPETRO", "name": "Hindustan Petroleum Corporation Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "HINDZINC", "name": "Hindustan Zinc Ltd.", "sector": "Metals & Mining"},
    {"symbol": "POWERINDIA", "name": "Hitachi Energy India Ltd.", "sector": "Capital Goods"},
    {"symbol": "HOMEFIRST", "name": "Home First Finance Company India Ltd.", "sector": "Financial Services"},
    {"symbol": "HONASA", "name": "Honasa Consumer Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "HONAUT", "name": "Honeywell Automation India Ltd.", "sector": "Capital Goods"},
    {"symbol": "HUDCO", "name": "Housing & Urban Development Corporation Ltd.", "sector": "Financial Services"},
    {"symbol": "HYUNDAI", "name": "Hyundai Motor India Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "ICICILIFE", "name": "ICICI Life Insurance Ltd.", "sector": "Financial Services"},
    {"symbol": "ICICIGI", "name": "ICICI Lombard General Insurance Company Ltd.", "sector": "Financial Services"},
    {"symbol": "ICICIAMC", "name": "ICICI Prudential Asset Management Company Ltd.", "sector": "Financial Services"},
    {"symbol": "IDBI", "name": "IDBI Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "IDFCFIRSTB", "name": "IDFC First Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "IFCI", "name": "IFCI Ltd.", "sector": "Financial Services"},
    {"symbol": "IIFL", "name": "IIFL Finance Ltd.", "sector": "Financial Services"},
    {"symbol": "INOXINDIA", "name": "INOX India Ltd.", "sector": "Capital Goods"},
    {"symbol": "IRB", "name": "IRB Infrastructure Developers Ltd.", "sector": "Construction"},
    {"symbol": "IRCON", "name": "IRCON International Ltd.", "sector": "Construction"},
    {"symbol": "ITCHOTELS", "name": "ITC Hotels Ltd.", "sector": "Consumer Services"},
    {"symbol": "ITC", "name": "ITC Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "ITI", "name": "ITI Ltd.", "sector": "Telecommunication"},
    {"symbol": "INDIACEM", "name": "India Cements Ltd.", "sector": "Construction Materials"},
    {"symbol": "INDIAMART", "name": "Indiamart Intermesh Ltd.", "sector": "Consumer Services"},
    {"symbol": "INDIANB", "name": "Indian Bank", "sector": "Financial Services"},
    {"symbol": "IEX", "name": "Indian Energy Exchange Ltd.", "sector": "Financial Services"},
    {"symbol": "INDHOTEL", "name": "Indian Hotels Co. Ltd.", "sector": "Consumer Services"},
    {"symbol": "IOC", "name": "Indian Oil Corporation Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "IOB", "name": "Indian Overseas Bank", "sector": "Financial Services"},
    {"symbol": "IRCTC", "name": "Indian Railway Catering And Tourism Corporation Ltd.", "sector": "Consumer Services"},
    {"symbol": "IRFC", "name": "Indian Railway Finance Corporation Ltd.", "sector": "Financial Services"},
    {"symbol": "IREDA", "name": "Indian Renewable Energy Development Agency Ltd.", "sector": "Financial Services"},
    {"symbol": "IGL", "name": "Indraprastha Gas Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "INDUSTOWER", "name": "Indus Towers Ltd.", "sector": "Telecommunication"},
    {"symbol": "INDUSINDBK", "name": "IndusInd Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "NAUKRI", "name": "Info Edge (India) Ltd.", "sector": "Consumer Services"},
    {"symbol": "INFY", "name": "Infosys Ltd.", "sector": "Information Technology"},
    {"symbol": "INOXWIND", "name": "Inox Wind Ltd.", "sector": "Capital Goods"},
    {"symbol": "INTELLECT", "name": "Intellect Design Arena Ltd.", "sector": "Information Technology"},
    {"symbol": "INDIGO", "name": "InterGlobe Aviation Ltd.", "sector": "Services"},
    {"symbol": "IGIL", "name": "International Gemological Institute Ltd.", "sector": "Services"},
    {"symbol": "IKS", "name": "Inventurus Knowledge Solutions Ltd.", "sector": "Information Technology"},
    {"symbol": "IPCALAB", "name": "Ipca Laboratories Ltd.", "sector": "Healthcare"},
    {"symbol": "JKCEMENT", "name": "J.K. Cement Ltd.", "sector": "Construction Materials"},
    {"symbol": "JBMA", "name": "JBM Auto Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "JKTYRE", "name": "JK Tyre & Industries Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "JMFINANCIL", "name": "JM Financial Ltd.", "sector": "Financial Services"},
    {"symbol": "JSWCEMENT", "name": "JSW Cement Ltd.", "sector": "Construction Materials"},
    {"symbol": "JSWENERGY", "name": "JSW Energy Ltd.", "sector": "Power"},
    {"symbol": "JSWINFRA", "name": "JSW Infrastructure Ltd.", "sector": "Services"},
    {"symbol": "JSWSTEEL", "name": "JSW Steel Ltd.", "sector": "Metals & Mining"},
    {"symbol": "JAINREC", "name": "Jain Resource Recycling Ltd.", "sector": "Metals & Mining"},
    {"symbol": "JPPOWER", "name": "Jaiprakash Power Ventures Ltd.", "sector": "Power"},
    {"symbol": "J&KBANK", "name": "Jammu & Kashmir Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "JINDALSAW", "name": "Jindal Saw Ltd.", "sector": "Capital Goods"},
    {"symbol": "JSL", "name": "Jindal Stainless Ltd.", "sector": "Metals & Mining"},
    {"symbol": "JINDALSTEL", "name": "Jindal Steel Ltd.", "sector": "Metals & Mining"},
    {"symbol": "JIOFIN", "name": "Jio Financial Services Ltd.", "sector": "Financial Services"},
    {"symbol": "JUBLFOOD", "name": "Jubilant Foodworks Ltd.", "sector": "Consumer Services"},
    {"symbol": "JUBLINGREA", "name": "Jubilant Ingrevia Ltd.", "sector": "Chemicals"},
    {"symbol": "JWL", "name": "Jupiter Wagons Ltd.", "sector": "Capital Goods"},
    {"symbol": "JYOTICNC", "name": "Jyoti CNC Automation Ltd.", "sector": "Capital Goods"},
    {"symbol": "KPRMILL", "name": "K.P.R. Mill Ltd.", "sector": "Textiles"},
    {"symbol": "KEI", "name": "KEI Industries Ltd.", "sector": "Capital Goods"},
    {"symbol": "KPITTECH", "name": "KPIT Technologies Ltd.", "sector": "Information Technology"},
    {"symbol": "KSB", "name": "KSB Ltd.", "sector": "Capital Goods"},
    {"symbol": "KAJARIACER", "name": "Kajaria Ceramics Ltd.", "sector": "Consumer Durables"},
    {"symbol": "KPIL", "name": "Kalpataru Projects International Ltd.", "sector": "Construction"},
    {"symbol": "KALYANKJIL", "name": "Kalyan Jewellers India Ltd.", "sector": "Consumer Durables"},
    {"symbol": "KARURVYSYA", "name": "Karur Vysya Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "KAYNES", "name": "Kaynes Technology India Ltd.", "sector": "Capital Goods"},
    {"symbol": "KEC", "name": "Kec International Ltd.", "sector": "Construction"},
    {"symbol": "KFINTECH", "name": "Kfin Technologies Ltd.", "sector": "Financial Services"},
    {"symbol": "KIRLOSBROS", "name": "Kirloskar Brothers Ltd.", "sector": "Capital Goods"},
    {"symbol": "KIRLOSENG", "name": "Kirloskar Oil Eng Ltd.", "sector": "Capital Goods"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "KIMS", "name": "Krishna Institute of Medical Sciences Ltd.", "sector": "Healthcare"},
    {"symbol": "LTF", "name": "L&T Finance Ltd.", "sector": "Financial Services"},
    {"symbol": "LTTS", "name": "L&T Technology Services Ltd.", "sector": "Information Technology"},
    {"symbol": "LGEINDIA", "name": "LG Electronics India Ltd.", "sector": "Consumer Durables"},
    {"symbol": "LICHSGFIN", "name": "LIC Housing Finance Ltd.", "sector": "Financial Services"},
    {"symbol": "LTFOODS", "name": "LT Foods Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "LTM", "name": "LTM Ltd.", "sector": "Information Technology"},
    {"symbol": "LT", "name": "Larsen & Toubro Ltd.", "sector": "Construction"},
    {"symbol": "LAURUSLABS", "name": "Laurus Labs Ltd.", "sector": "Healthcare"},
    {"symbol": "LEMONTREE", "name": "Lemon Tree Hotels Ltd.", "sector": "Consumer Services"},
    {"symbol": "LENSKART", "name": "Lenskart Solutions Ltd.", "sector": "Consumer Services"},
    {"symbol": "LICI", "name": "Life Insurance Corporation of India", "sector": "Financial Services"},
    {"symbol": "LINDEINDIA", "name": "Linde India Ltd.", "sector": "Chemicals"},
    {"symbol": "LLOYDSME", "name": "Lloyds Metals And Energy Ltd.", "sector": "Metals & Mining"},
    {"symbol": "LODHA", "name": "Lodha Developers Ltd.", "sector": "Realty"},
    {"symbol": "LUPIN", "name": "Lupin Ltd.", "sector": "Healthcare"},
    {"symbol": "MMTC", "name": "MMTC Ltd.", "sector": "Services"},
    {"symbol": "MRF", "name": "MRF Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "MTARTECH", "name": "MTAR Technologies Ltd.", "sector": "Capital Goods"},
    {"symbol": "MGL", "name": "Mahanagar Gas Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "M&MFIN", "name": "Mahindra & Mahindra Financial Services Ltd.", "sector": "Financial Services"},
    {"symbol": "M&M", "name": "Mahindra & Mahindra Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "MANAPPURAM", "name": "Manappuram Finance Ltd.", "sector": "Financial Services"},
    {"symbol": "MRPL", "name": "Mangalore Refinery & Petrochemicals Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "MANKIND", "name": "Mankind Pharma Ltd.", "sector": "Healthcare"},
    {"symbol": "MARICO", "name": "Marico Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki India Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "MFSL", "name": "Max Financial Services Ltd.", "sector": "Financial Services"},
    {"symbol": "MAXHEALTH", "name": "Max Healthcare Institute Ltd.", "sector": "Healthcare"},
    {"symbol": "MAZDOCK", "name": "Mazagoan Dock Shipbuilders Ltd.", "sector": "Capital Goods"},
    {"symbol": "MEESHO", "name": "Meesho Ltd.", "sector": "Consumer Services"},
    {"symbol": "MINDACORP", "name": "Minda Corporation Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "MSUMI", "name": "Motherson Sumi Wiring India Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "MOTILALOFS", "name": "Motilal Oswal Financial Services Ltd.", "sector": "Financial Services"},
    {"symbol": "MPHASIS", "name": "MphasiS Ltd.", "sector": "Information Technology"},
    {"symbol": "MCX", "name": "Multi Commodity Exchange of India Ltd.", "sector": "Financial Services"},
    {"symbol": "MUTHOOTFIN", "name": "Muthoot Finance Ltd.", "sector": "Financial Services"},
    {"symbol": "NATCOPHARM", "name": "NATCO Pharma Ltd.", "sector": "Healthcare"},
    {"symbol": "NBCC", "name": "NBCC (India) Ltd.", "sector": "Construction"},
    {"symbol": "NCC", "name": "NCC Ltd.", "sector": "Construction"},
    {"symbol": "NHPC", "name": "NHPC Ltd.", "sector": "Power"},
    {"symbol": "NLCINDIA", "name": "NLC India Ltd.", "sector": "Power"},
    {"symbol": "NMDC", "name": "NMDC Ltd.", "sector": "Metals & Mining"},
    {"symbol": "NSLNISP", "name": "NMDC Steel Ltd.", "sector": "Metals & Mining"},
    {"symbol": "NTPCGREEN", "name": "NTPC Green Energy Ltd.", "sector": "Power"},
    {"symbol": "NTPC", "name": "NTPC Ltd.", "sector": "Power"},
    {"symbol": "NH", "name": "Narayana Hrudayalaya Ltd.", "sector": "Healthcare"},
    {"symbol": "NATIONALUM", "name": "National Aluminium Co. Ltd.", "sector": "Metals & Mining"},
    {"symbol": "NAVA", "name": "Nava Ltd.", "sector": "Power"},
    {"symbol": "NAVINFLUOR", "name": "Navin Fluorine International Ltd.", "sector": "Chemicals"},
    {"symbol": "NESTLEIND", "name": "Nestle India Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "NETWEB", "name": "Netweb Technologies India Ltd.", "sector": "Information Technology"},
    {"symbol": "NEULANDLAB", "name": "Neuland Laboratories Ltd.", "sector": "Healthcare"},
    {"symbol": "NAM-INDIA", "name": "Nippon Life India Asset Management Ltd.", "sector": "Financial Services"},
    {"symbol": "NUVAMA", "name": "Nuvama Wealth Management Ltd.", "sector": "Financial Services"},
    {"symbol": "NUVOCO", "name": "Nuvoco Vistas Corporation Ltd.", "sector": "Construction Materials"},
    {"symbol": "OBEROIRLTY", "name": "Oberoi Realty Ltd.", "sector": "Realty"},
    {"symbol": "ONGC", "name": "Oil & Natural Gas Corporation Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "OIL", "name": "Oil India Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "OLAELEC", "name": "Ola Electric Mobility Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "OLECTRA", "name": "Olectra Greentech Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "PAYTM", "name": "One 97 Communications Ltd.", "sector": "Financial Services"},
    {"symbol": "ONESOURCE", "name": "Onesource Specialty Pharma Ltd.", "sector": "Healthcare"},
    {"symbol": "OFSS", "name": "Oracle Financial Services Software Ltd.", "sector": "Information Technology"},
    {"symbol": "POLICYBZR", "name": "PB Fintech Ltd.", "sector": "Financial Services"},
    {"symbol": "PCBL", "name": "PCBL Chemical Ltd.", "sector": "Chemicals"},
    {"symbol": "PGEL", "name": "PG Electroplast Ltd.", "sector": "Consumer Durables"},
    {"symbol": "PIIND", "name": "PI Industries Ltd.", "sector": "Chemicals"},
    {"symbol": "PNBHOUSING", "name": "PNB Housing Finance Ltd.", "sector": "Financial Services"},
    {"symbol": "PTCIL", "name": "PTC Industries Ltd.", "sector": "Capital Goods"},
    {"symbol": "PVRINOX", "name": "PVR INOX Ltd.", "sector": "Media Entertainment & Publication"},
    {"symbol": "PAGEIND", "name": "Page Industries Ltd.", "sector": "Textiles"},
    {"symbol": "PARADEEP", "name": "Paradeep Phosphates Ltd.", "sector": "Chemicals"},
    {"symbol": "PATANJALI", "name": "Patanjali Foods Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "PERSISTENT", "name": "Persistent Systems Ltd.", "sector": "Information Technology"},
    {"symbol": "PETRONET", "name": "Petronet LNG Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "PHOENIXLTD", "name": "Phoenix Mills Ltd.", "sector": "Realty"},
    {"symbol": "PWL", "name": "Physicswallah Ltd.", "sector": "Consumer Services"},
    {"symbol": "PIDILITIND", "name": "Pidilite Industries Ltd.", "sector": "Chemicals"},
    {"symbol": "PINELABS", "name": "Pine Labs Ltd.", "sector": "Financial Services"},
    {"symbol": "PIRAMALFIN", "name": "Piramal Finance Ltd.", "sector": "Financial Services"},
    {"symbol": "PPLPHARMA", "name": "Piramal Pharma Ltd.", "sector": "Healthcare"},
    {"symbol": "POLYMED", "name": "Poly Medicure Ltd.", "sector": "Healthcare"},
    {"symbol": "POLYCAB", "name": "Polycab India Ltd.", "sector": "Capital Goods"},
    {"symbol": "POONAWALLA", "name": "Poonawalla Fincorp Ltd.", "sector": "Financial Services"},
    {"symbol": "PFC", "name": "Power Finance Corporation Ltd.", "sector": "Financial Services"},
    {"symbol": "POWERGRID", "name": "Power Grid Corporation of India Ltd.", "sector": "Power"},
    {"symbol": "PREMIERENE", "name": "Premier Energies Ltd.", "sector": "Capital Goods"},
    {"symbol": "PRESTIGE", "name": "Prestige Estates Projects Ltd.", "sector": "Realty"},
    {"symbol": "PFOCUS", "name": "Prime Focus Ltd.", "sector": "Media Entertainment & Publication"},
    {"symbol": "PRIVISCL", "name": "Privi Speciality Chemicals Ltd.", "sector": "Chemicals"},
    {"symbol": "PNB", "name": "Punjab National Bank", "sector": "Financial Services"},
    {"symbol": "RRKABEL", "name": "R R Kabel Ltd.", "sector": "Capital Goods"},
    {"symbol": "RBLBANK", "name": "RBL Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "RECLTD", "name": "REC Ltd.", "sector": "Financial Services"},
    {"symbol": "RHIM", "name": "RHI MAGNESITA INDIA LTD.", "sector": "Capital Goods"},
    {"symbol": "RITES", "name": "RITES Ltd.", "sector": "Construction"},
    {"symbol": "RADICO", "name": "Radico Khaitan Ltd", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "RVNL", "name": "Rail Vikas Nigam Ltd.", "sector": "Construction"},
    {"symbol": "RAILTEL", "name": "Railtel Corporation Of India Ltd.", "sector": "Telecommunication"},
    {"symbol": "RAINBOW", "name": "Rainbow Childrens Medicare Ltd.", "sector": "Healthcare"},
    {"symbol": "RKFORGE", "name": "Ramkrishna Forgings Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "REDINGTON", "name": "Redington Ltd.", "sector": "Services"},
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "RPOWER", "name": "Reliance Power Ltd.", "sector": "Power"},
    {"symbol": "RUBICON", "name": "Rubicon Research Ltd.", "sector": "Healthcare"},
    {"symbol": "SBICARD", "name": "SBI Cards and Payment Services Ltd.", "sector": "Financial Services"},
    {"symbol": "SBILIFE", "name": "SBI Life Insurance Company Ltd.", "sector": "Financial Services"},
    {"symbol": "SJVN", "name": "SJVN Ltd.", "sector": "Power"},
    {"symbol": "SHRIPISTON", "name": "SPR Auto Technologies Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "SRF", "name": "SRF Ltd.", "sector": "Chemicals"},
    {"symbol": "SAGILITY", "name": "Sagility Ltd.", "sector": "Information Technology"},
    {"symbol": "SAILIFE", "name": "Sai Life Sciences Ltd.", "sector": "Healthcare"},
    {"symbol": "SAMMAANCAP", "name": "Sammaan Capital Ltd.", "sector": "Financial Services"},
    {"symbol": "MOTHERSON", "name": "Samvardhana Motherson International Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "SANSERA", "name": "Sansera Engineering Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "SAREGAMA", "name": "Saregama India Ltd.", "sector": "Media Entertainment & Publication"},
    {"symbol": "SARDAEN", "name": "Sarda Energy and Minerals Ltd.", "sector": "Metals & Mining"},
    {"symbol": "SCHAEFFLER", "name": "Schaeffler India Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "SCHNEIDER", "name": "Schneider Electric Infrastructure Ltd.", "sector": "Capital Goods"},
    {"symbol": "SCI", "name": "Shipping Corporation of India Ltd.", "sector": "Services"},
    {"symbol": "SHREECEM", "name": "Shree Cement Ltd.", "sector": "Construction Materials"},
    {"symbol": "SHRIRAMFIN", "name": "Shriram Finance Ltd.", "sector": "Financial Services"},
    {"symbol": "SHYAMMETL", "name": "Shyam Metalics and Energy Ltd.", "sector": "Capital Goods"},
    {"symbol": "ENRIN", "name": "Siemens Energy India Ltd.", "sector": "Capital Goods"},
    {"symbol": "SIEMENS", "name": "Siemens Ltd.", "sector": "Capital Goods"},
    {"symbol": "SIGNATURE", "name": "Signatureglobal (India) Ltd.", "sector": "Realty"},
    {"symbol": "SOBHA", "name": "Sobha Ltd.", "sector": "Realty"},
    {"symbol": "SOLARINDS", "name": "Solar Industries India Ltd.", "sector": "Chemicals"},
    {"symbol": "SONACOMS", "name": "Sona BLW Precision Forgings Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "STARHEALTH", "name": "Star Health and Allied Insurance Company Ltd.", "sector": "Financial Services"},
    {"symbol": "SBIN", "name": "State Bank of India", "sector": "Financial Services"},
    {"symbol": "SAIL", "name": "Steel Authority of India Ltd.", "sector": "Metals & Mining"},
    {"symbol": "STLTECH", "name": "Sterlite Technologies Ltd.", "sector": "Telecommunication"},
    {"symbol": "SUMICHEM", "name": "Sumitomo Chemical India Ltd.", "sector": "Chemicals"},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd.", "sector": "Healthcare"},
    {"symbol": "SUNTV", "name": "Sun TV Network Ltd.", "sector": "Media Entertainment & Publication"},
    {"symbol": "SUNDARMFIN", "name": "Sundaram Finance Ltd.", "sector": "Financial Services"},
    {"symbol": "SUPREMEIND", "name": "Supreme Industries Ltd.", "sector": "Capital Goods"},
    {"symbol": "SUZLON", "name": "Suzlon Energy Ltd.", "sector": "Capital Goods"},
    {"symbol": "SWANCORP", "name": "Swan Corp Ltd.", "sector": "Chemicals"},
    {"symbol": "SWIGGY", "name": "Swiggy Ltd.", "sector": "Consumer Services"},
    {"symbol": "SYNGENE", "name": "Syngene International Ltd.", "sector": "Healthcare"},
    {"symbol": "SYRMA", "name": "Syrma SGS Technology Ltd.", "sector": "Capital Goods"},
    {"symbol": "TBOTEK", "name": "TBO Tek Ltd.", "sector": "Consumer Services"},
    {"symbol": "TDPOWERSYS", "name": "TD Power Systems Ltd.", "sector": "Capital Goods"},
    {"symbol": "TVSMOTOR", "name": "TVS Motor Company Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "TATACAP", "name": "Tata Capital Ltd.", "sector": "Financial Services"},
    {"symbol": "TATACHEM", "name": "Tata Chemicals Ltd.", "sector": "Chemicals"},
    {"symbol": "TATACOMM", "name": "Tata Communications Ltd.", "sector": "Telecommunication"},
    {"symbol": "TCS", "name": "Tata Consultancy Services Ltd.", "sector": "Information Technology"},
    {"symbol": "TATACONSUM", "name": "Tata Consumer Products Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "TATAELXSI", "name": "Tata Elxsi Ltd.", "sector": "Information Technology"},
    {"symbol": "TATAINVEST", "name": "Tata Investment Corporation Ltd.", "sector": "Financial Services"},
    {"symbol": "TMCV", "name": "Tata Motors Ltd.", "sector": "Capital Goods"},
    {"symbol": "TMPV", "name": "Tata Motors Passenger Vehicles Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "TATAPOWER", "name": "Tata Power Co. Ltd.", "sector": "Power"},
    {"symbol": "TATASTEEL", "name": "Tata Steel Ltd.", "sector": "Metals & Mining"},
    {"symbol": "TATATECH", "name": "Tata Technologies Ltd.", "sector": "Information Technology"},
    {"symbol": "TTML", "name": "Tata Teleservices (Maharashtra) Ltd.", "sector": "Telecommunication"},
    {"symbol": "TECHM", "name": "Tech Mahindra Ltd.", "sector": "Information Technology"},
    {"symbol": "TECHNOE", "name": "Techno Electric & Engineering Company Ltd.", "sector": "Construction"},
    {"symbol": "TEGA", "name": "Tega Industries Ltd.", "sector": "Capital Goods"},
    {"symbol": "TEJASNET", "name": "Tejas Networks Ltd.", "sector": "Telecommunication"},
    {"symbol": "TENNIND", "name": "Tenneco Clean Air India Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "THANGAMAYL", "name": "Thangamayil Jewellery Ltd.", "sector": "Consumer Durables"},
    {"symbol": "NIACL", "name": "The New India Assurance Company Ltd.", "sector": "Financial Services"},
    {"symbol": "RAMCOCEM", "name": "The Ramco Cements Ltd.", "sector": "Construction Materials"},
    {"symbol": "THERMAX", "name": "Thermax Ltd.", "sector": "Capital Goods"},
    {"symbol": "TIMKEN", "name": "Timken India Ltd.", "sector": "Capital Goods"},
    {"symbol": "TITAGARH", "name": "Titagarh Rail Systems Ltd.", "sector": "Capital Goods"},
    {"symbol": "TITAN", "name": "Titan Company Ltd.", "sector": "Consumer Durables"},
    {"symbol": "TORNTPHARM", "name": "Torrent Pharmaceuticals Ltd.", "sector": "Healthcare"},
    {"symbol": "TORNTPOWER", "name": "Torrent Power Ltd.", "sector": "Power"},
    {"symbol": "TARIL", "name": "Transformers And Rectifiers (India) Ltd.", "sector": "Capital Goods"},
    {"symbol": "TRENT", "name": "Trent Ltd.", "sector": "Consumer Services"},
    {"symbol": "TRIDENT", "name": "Trident Ltd.", "sector": "Textiles"},
    {"symbol": "TRITURBINE", "name": "Triveni Turbine Ltd.", "sector": "Capital Goods"},
    {"symbol": "TIINDIA", "name": "Tube Investments of India Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "UCOBANK", "name": "UCO Bank", "sector": "Financial Services"},
    {"symbol": "UNOMINDA", "name": "UNO Minda Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "UPL", "name": "UPL Ltd.", "sector": "Chemicals"},
    {"symbol": "UTIAMC", "name": "UTI Asset Management Company Ltd.", "sector": "Financial Services"},
    {"symbol": "ULTRACEMCO", "name": "UltraTech Cement Ltd.", "sector": "Construction Materials"},
    {"symbol": "UNIONBANK", "name": "Union Bank of India", "sector": "Financial Services"},
    {"symbol": "UBL", "name": "United Breweries Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "UNITDSPR", "name": "United Spirits Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "URBANCO", "name": "Urban Company Ltd.", "sector": "Consumer Services"},
    {"symbol": "USHAMART", "name": "Usha Martin Ltd.", "sector": "Capital Goods"},
    {"symbol": "VTL", "name": "Vardhman Textiles Ltd.", "sector": "Textiles"},
    {"symbol": "VBL", "name": "Varun Beverages Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "VAML", "name": "Vedanta Aluminium Metal Ltd.", "sector": "Metals & Mining"},
    {"symbol": "VISL", "name": "Vedanta Iron and Steel Ltd.", "sector": "Metals & Mining"},
    {"symbol": "VEDL", "name": "Vedanta Ltd.", "sector": "Metals & Mining"},
    {"symbol": "VOGL", "name": "Vedanta Oil and Gas Ltd.", "sector": "Oil Gas & Consumable Fuels"},
    {"symbol": "VEDPOWER", "name": "Vedanta Power Ltd.", "sector": "Power"},
    {"symbol": "VIJAYA", "name": "Vijaya Diagnostic Centre Ltd.", "sector": "Healthcare"},
    {"symbol": "VMM", "name": "Vishal Mega Mart Ltd.", "sector": "Consumer Services"},
    {"symbol": "IDEA", "name": "Vodafone Idea Ltd.", "sector": "Telecommunication"},
    {"symbol": "VOLTAS", "name": "Voltas Ltd.", "sector": "Consumer Durables"},
    {"symbol": "WAAREEENER", "name": "Waaree Energies Ltd.", "sector": "Capital Goods"},
    {"symbol": "WELCORP", "name": "Welspun Corp Ltd.", "sector": "Capital Goods"},
    {"symbol": "WELSPUNLIV", "name": "Welspun Living Ltd.", "sector": "Textiles"},
    {"symbol": "WHIRLPOOL", "name": "Whirlpool of India Ltd.", "sector": "Consumer Durables"},
    {"symbol": "WIPRO", "name": "Wipro Ltd.", "sector": "Information Technology"},
    {"symbol": "WOCKPHARMA", "name": "Wockhardt Ltd.", "sector": "Healthcare"},
    {"symbol": "YESBANK", "name": "Yes Bank Ltd.", "sector": "Financial Services"},
    {"symbol": "ZFCVINDIA", "name": "ZF Commercial Vehicle Control Systems India Ltd.", "sector": "Automobile and Auto Components"},
    {"symbol": "ZEEL", "name": "Zee Entertainment Enterprises Ltd.", "sector": "Media Entertainment & Publication"},
    {"symbol": "ZENTEC", "name": "Zen Technologies Ltd.", "sector": "Capital Goods"},
    {"symbol": "ZENSARTECH", "name": "Zensar Technolgies Ltd.", "sector": "Information Technology"},
    {"symbol": "ZYDUSLIFE", "name": "Zydus Lifesciences Ltd.", "sector": "Healthcare"},
    {"symbol": "ZYDUSWELL", "name": "Zydus Wellness Ltd.", "sector": "Fast Moving Consumer Goods"},
    {"symbol": "ECLERX", "name": "eClerx Services Ltd.", "sector": "Services"},
]


def fetch_nifty500_from_nse() -> list:
    """Fetches the latest official Nifty 500 constituent list from NSE India archives."""
    try:
        req = urllib.request.Request(
            NSE_NIFTY500_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = [line.decode("utf-8", errors="ignore") for line in resp.readlines()]
            reader = csv.DictReader(content)
            clean_list = []
            seen = set()
            for r in reader:
                sym = r.get("Symbol", "").strip()
                name = r.get("Company Name", "").strip()
                sector = r.get("Industry", "").strip()
                if not sym or sym == "BAGMANE":
                    continue
                if sym == "DUMMYHEG":
                    sym = "HEG"
                    name = "HEG Ltd."
                if sym not in seen:
                    seen.add(sym)
                    clean_list.append({"symbol": sym, "name": name, "sector": sector})
            if len(clean_list) >= 490:
                return clean_list
    except Exception as e:
        print(f"[Dynamic Universe] Note: NSE fetch fallback to built-in universe ({e})")
    return MASTER_NSE_UNIVERSE

def load_cached_universe() -> dict:
    """Loads dynamically discovered universe from disk."""
    if os.path.exists(UNIVERSE_CACHE_FILE):
        try:
            with open(UNIVERSE_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data and isinstance(data, dict) and "stocks" in data and len(data["stocks"]) >= 500:
                    return data
        except Exception as e:
            print(f"Error loading dynamic universe cache: {e}")
    return None

def save_cached_universe(data: dict):
    """Saves dynamic universe to disk."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(UNIVERSE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving dynamic universe cache: {e}")

def get_active_universe() -> list:
    """
    Returns the currently active dynamic universe.
    If cached universe with full Nifty 500 constituents exists, returns it;
    otherwise initializes cache with master Nifty 500 universe.
    """
    cached = load_cached_universe()
    if cached and "stocks" in cached and len(cached["stocks"]) >= 500:
        return cached["stocks"]
    
    # Initialize cache with master Nifty 500 universe
    initial_data = {
        "status": "active",
        "last_updated": datetime.now().isoformat(),
        "total_stocks": len(MASTER_NSE_UNIVERSE),
        "source": "NSE Nifty 500 Official Universe",
        "stocks": MASTER_NSE_UNIVERSE
    }
    save_cached_universe(initial_data)
    return MASTER_NSE_UNIVERSE

def refresh_dynamic_momentum_universe(top_n: int = 500) -> dict:
    """
    Scans the Nifty 500 universe, calculates momentum scores across constituents,
    and updates the dynamic universe sorted by momentum leaders.
    """
    from algo_engine import fetch_stock_data
    
    universe = MASTER_NSE_UNIVERSE
    print(f"[Dynamic Universe] Initiating momentum discovery across {len(universe)} Nifty 500 stocks...")
    scored_stocks = []
    
    def score_worker(item):
        sym = item["symbol"]
        try:
            df = fetch_stock_data(sym, range_str="6mo", interval="1d")
            if df.empty or len(df) < 45:
                return {**item, "momentum_score": -999.0}
            
            c_curr = float(df["close"].iloc[-1])
            c_20 = float(df["close"].iloc[-20]) if len(df) >= 20 else c_curr
            c_60 = float(df["close"].iloc[-45]) if len(df) >= 45 else c_curr
            
            roc20 = round(((c_curr - c_20) / c_20) * 100.0, 2)
            roc60 = round(((c_curr - c_60) / c_60) * 100.0, 2)
            
            h52 = float(df["high"].max())
            pct_from_high = round(((h52 - c_curr) / h52) * 100.0, 2)
            
            vol = float(df["volume"].iloc[-1])
            v_ma = float(df["vol_sma20"].iloc[-1]) if not pd.isna(df["vol_sma20"].iloc[-1]) else vol
            vol_ratio = round(vol / (v_ma + 1e-9), 2)
            
            # Stan Weinstein Stage 2 & Momentum Composite Score
            score = (roc20 * 0.40) + (roc60 * 0.35) + (max(0, 25 - pct_from_high) * 0.25)
            
            return {
                **item,
                "roc20": roc20,
                "roc60": roc60,
                "pct_from_52w_high": pct_from_high,
                "vol_ratio": vol_ratio,
                "momentum_score": round(score, 2)
            }
        except Exception:
            return {**item, "momentum_score": -999.0}
    
    with ThreadPoolExecutor(max_workers=35) as executor:
        results = executor.map(score_worker, universe)
        for r in results:
            if r:
                scored_stocks.append(r)
                
    # Sort descending by composite momentum score
    scored_stocks.sort(key=lambda x: x.get("momentum_score", -999), reverse=True)
    
    # Keep top_n or full universe
    selected = scored_stocks[:top_n] if top_n and len(scored_stocks) >= top_n else scored_stocks
    
    clean_stocks = [{"symbol": s["symbol"], "name": s["name"], "sector": s["sector"]} for s in selected]
    top_leaders = [s["symbol"] for s in selected if s.get("momentum_score", -999) > -990][:25]
    
    result_data = {
        "status": "success",
        "last_updated": datetime.now().isoformat(),
        "total_stocks": len(clean_stocks),
        "top_momentum_leaders": top_leaders,
        "stocks": clean_stocks
    }
    save_cached_universe(result_data)
    print(f"[Dynamic Universe] Nifty 500 Refreshed successfully! Top momentum leaders: {top_leaders[:10]}")
    return result_data
