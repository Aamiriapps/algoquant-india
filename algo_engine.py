import requests
import json
import time
import os
import sys
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
import numpy as np
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from dynamic_universe import get_active_universe, MASTER_NSE_UNIVERSE
except ImportError:
    get_active_universe = None
    MASTER_NSE_UNIVERSE = None

# ==============================================================================
# MASTER LIQUID UNIVERSE (NSE NIFTY 500 + DYNAMIC MOMENTUM LEADERS)
# Filtered for institutional volume, high liquidity, zero penny stocks.
# ==============================================================================
LIQUID_UNIVERSE = [
    # Top 50 Mega Caps
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd", "sector": "Energy / Conglomerate"},
    {"symbol": "TCS", "name": "Tata Consultancy Services Ltd", "sector": "Information Technology"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "sector": "Banking"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd", "sector": "Banking"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd", "sector": "Telecom"},
    {"symbol": "INFY", "name": "Infosys Ltd", "sector": "Information Technology"},
    {"symbol": "SBIN", "name": "State Bank of India", "sector": "Banking"},
    {"symbol": "ITC", "name": "ITC Ltd", "sector": "FMCG / Diversified"},
    {"symbol": "LT", "name": "Larsen & Toubro Ltd", "sector": "Infrastructure / Capital Goods"},
    {"symbol": "TMPV", "name": "Tata Motors Passenger Vehicles Ltd", "sector": "Automobile"},
    {"symbol": "TMCV", "name": "Tata Motors Commercial Vehicles Ltd", "sector": "Automobile"},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd", "sector": "FMCG"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd", "sector": "NBFC / Financial Services"},
    {"symbol": "AXISBANK", "name": "Axis Bank Ltd", "sector": "Banking"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank Ltd", "sector": "Banking"},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd", "sector": "Pharma"},
    {"symbol": "TITAN", "name": "Titan Company Ltd", "sector": "Consumer Goods / Jewellery"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki India Ltd", "sector": "Automobile"},
    {"symbol": "NTPC", "name": "NTPC Ltd", "sector": "Power / Utilities"},
    {"symbol": "ONGC", "name": "Oil & Natural Gas Corp Ltd", "sector": "Energy / Oil & Gas"},
    {"symbol": "TATASTEEL", "name": "Tata Steel Ltd", "sector": "Metals & Mining"},
    {"symbol": "POWERGRID", "name": "Power Grid Corporation of India Ltd", "sector": "Power / Utilities"},
    {"symbol": "M&M", "name": "Mahindra & Mahindra Ltd", "sector": "Automobile"},
    {"symbol": "ADANIPORTS", "name": "Adani Ports and SEZ Ltd", "sector": "Ports & Logistics"},
    {"symbol": "ADANIENT", "name": "Adani Enterprises Ltd", "sector": "Diversified / Commodities"},
    {"symbol": "COALINDIA", "name": "Coal India Ltd", "sector": "Mining / Energy"},
    {"symbol": "BEL", "name": "Bharat Electronics Ltd", "sector": "Defence / Electronics"},
    {"symbol": "HAL", "name": "Hindustan Aeronautics Ltd", "sector": "Defence / Aerospace"},
    {"symbol": "TRENT", "name": "Trent Ltd", "sector": "Retail"},
    {"symbol": "ETERNAL", "name": "Eternal Ltd (formerly Zomato)", "sector": "Internet / Consumer Tech"},
    {"symbol": "VBL", "name": "Varun Beverages Ltd", "sector": "Beverages / FMCG"},
    {"symbol": "DLF", "name": "DLF Ltd", "sector": "Real Estate"},
    {"symbol": "BAJAJ-AUTO", "name": "Bajaj Auto Ltd", "sector": "Automobile"},
    {"symbol": "GRASIM", "name": "Grasim Industries Ltd", "sector": "Materials / Cement"},
    {"symbol": "HINDALCO", "name": "Hindalco Industries Ltd", "sector": "Metals / Aluminium"},
    {"symbol": "TECHM", "name": "Tech Mahindra Ltd", "sector": "Information Technology"},
    {"symbol": "WIPRO", "name": "Wipro Ltd", "sector": "Information Technology"},
    {"symbol": "JSWSTEEL", "name": "JSW Steel Ltd", "sector": "Metals & Mining"},
    {"symbol": "CIPLA", "name": "Cipla Ltd", "sector": "Pharma"},
    {"symbol": "APOLLOHOSP", "name": "Apollo Hospitals Enterprise Ltd", "sector": "Healthcare"},
    {"symbol": "DRREDDY", "name": "Dr. Reddy's Laboratories Ltd", "sector": "Pharma"},
    {"symbol": "EICHERMOT", "name": "Eicher Motors Ltd", "sector": "Automobile"},
    {"symbol": "ULTRACEMCO", "name": "UltraTech Cement Ltd", "sector": "Cement"},
    {"symbol": "HEROMOTOCO", "name": "Hero MotoCorp Ltd", "sector": "Automobile"},
    {"symbol": "DIVISLAB", "name": "Divi's Laboratories Ltd", "sector": "Pharma"},
    {"symbol": "TATACONSUM", "name": "Tata Consumer Products Ltd", "sector": "FMCG"},
    {"symbol": "SBILIFE", "name": "SBI Life Insurance Co Ltd", "sector": "Insurance"},
    {"symbol": "HDFCLIFE", "name": "HDFC Life Insurance Co Ltd", "sector": "Insurance"},
    {"symbol": "SHRIRAMFIN", "name": "Shriram Finance Ltd", "sector": "NBFC"},
    {"symbol": "BPCL", "name": "Bharat Petroleum Corp Ltd", "sector": "Energy / Refining"},
    {"symbol": "BRITANNIA", "name": "Britannia Industries Ltd", "sector": "FMCG / Food"},
    
    # Next 50 Large Caps (Rank 51 - 100)
    {"symbol": "VEDL", "name": "Vedanta Ltd", "sector": "Metals & Mining"},
    {"symbol": "PIDILITIND", "name": "Pidilite Industries Ltd", "sector": "Specialty Chemicals"},
    {"symbol": "CHOLAFIN", "name": "Cholamandalam Investment & Finance", "sector": "NBFC"},
    {"symbol": "TVSMOTOR", "name": "TVS Motor Company Ltd", "sector": "Automobile"},
    {"symbol": "HAVELLS", "name": "Havells India Ltd", "sector": "Electrical Consumer Goods"},
    {"symbol": "GODREJCP", "name": "Godrej Consumer Products Ltd", "sector": "FMCG"},
    {"symbol": "INDUSINDBK", "name": "IndusInd Bank Ltd", "sector": "Banking"},
    {"symbol": "SIEMENS", "name": "Siemens Ltd", "sector": "Capital Goods"},
    {"symbol": "ABB", "name": "ABB India Ltd", "sector": "Capital Goods / Engineering"},
    {"symbol": "POLYCAB", "name": "Polycab India Ltd", "sector": "Cables & Wires"},
    {"symbol": "AMBUJACEM", "name": "Ambuja Cements Ltd", "sector": "Cement"},
    {"symbol": "BAJAJFINSV", "name": "Bajaj Finserv Ltd", "sector": "Financial Services"},
    {"symbol": "ASIANPAINT", "name": "Asian Paints Ltd", "sector": "Paints"},
    {"symbol": "NESTLEIND", "name": "Nestle India Ltd", "sector": "FMCG / Food"},
    {"symbol": "INDIGO", "name": "InterGlobe Aviation Ltd", "sector": "Aviation"},
    {"symbol": "IOC", "name": "Indian Oil Corporation Ltd", "sector": "Energy / Refining"},
    {"symbol": "GAIL", "name": "GAIL (India) Ltd", "sector": "Gas / Utilities"},
    {"symbol": "BOSCHLTD", "name": "Bosch Ltd", "sector": "Auto Ancillary"},
    {"symbol": "PERSISTENT", "name": "Persistent Systems Ltd", "sector": "Information Technology"},
    {"symbol": "COLPAL", "name": "Colgate-Palmolive (India) Ltd", "sector": "FMCG"},
    {"symbol": "DABUR", "name": "Dabur India Ltd", "sector": "FMCG"},
    {"symbol": "LICI", "name": "Life Insurance Corporation of India", "sector": "Insurance"},
    {"symbol": "MAXHEALTH", "name": "Max Healthcare Institute Ltd", "sector": "Healthcare"},
    {"symbol": "INDHOTEL", "name": "The Indian Hotels Co Ltd (Taj)", "sector": "Hospitality"},
    {"symbol": "CUMMINSIND", "name": "Cummins India Ltd", "sector": "Capital Goods / Diesel Engines"},
    {"symbol": "POLICYBZR", "name": "PB Fintech Ltd (Policybazaar)", "sector": "FinTech / Insurance"},
    {"symbol": "TATAPOWER", "name": "Tata Power Co Ltd", "sector": "Power / Utilities"},
    {"symbol": "RECLTD", "name": "REC Ltd", "sector": "NBFC / Power Finance"},
    {"symbol": "PFC", "name": "Power Finance Corporation Ltd", "sector": "NBFC / Power Finance"},
    {"symbol": "TIINDIA", "name": "Tube Investments of India Ltd", "sector": "Auto Ancillary"},
    {"symbol": "CGPOWER", "name": "CG Power and Industrial Solutions", "sector": "Electrical Equipment"},
    {"symbol": "SUZLON", "name": "Suzlon Energy Ltd", "sector": "Renewable Energy"},
    {"symbol": "FEDERALBNK", "name": "The Federal Bank Ltd", "sector": "Banking"},
    {"symbol": "IDFCFIRSTB", "name": "IDFC First Bank Ltd", "sector": "Banking"},
    {"symbol": "BANKBARODA", "name": "Bank of Baroda", "sector": "Banking"},
    {"symbol": "PNB", "name": "Punjab National Bank", "sector": "Banking"},
    {"symbol": "CANBK", "name": "Canara Bank", "sector": "Banking"},
    {"symbol": "UNIONBANK", "name": "Union Bank of India", "sector": "Banking"},
    {"symbol": "JINDALSTEL", "name": "Jindal Steel & Power Ltd", "sector": "Metals & Mining"},
    {"symbol": "SAIL", "name": "Steel Authority of India Ltd", "sector": "Metals & Mining"},
    {"symbol": "NMDC", "name": "NMDC Ltd", "sector": "Mining / Iron Ore"},
    {"symbol": "NATIONALUM", "name": "National Aluminium Co Ltd", "sector": "Metals / Aluminium"},
    {"symbol": "AUROPHARMA", "name": "Aurobindo Pharma Ltd", "sector": "Pharma"},
    {"symbol": "LUPIN", "name": "Lupin Ltd", "sector": "Pharma"},
    {"symbol": "ALKEM", "name": "Alkem Laboratories Ltd", "sector": "Pharma"},
    {"symbol": "TORNTPHARM", "name": "Torrent Pharmaceuticals Ltd", "sector": "Pharma"},
    {"symbol": "MANKIND", "name": "Mankind Pharma Ltd", "sector": "Pharma"},
    {"symbol": "ZYDUSLIFE", "name": "Zydus Lifesciences Ltd", "sector": "Pharma"},
    {"symbol": "BIOCON", "name": "Biocon Ltd", "sector": "Biotech / Pharma"},
    {"symbol": "SYNGENE", "name": "Syngene International Ltd", "sector": "CRO / Research"},

    # Top Mid Caps & Leaders (Rank 101 - 200)
    {"symbol": "ASTRAL", "name": "Astral Ltd", "sector": "Building Materials / Pipes"},
    {"symbol": "SUPREMEIND", "name": "Supreme Industries Ltd", "sector": "Plastics / Pipes"},
    {"symbol": "PIIND", "name": "PI Industries Ltd", "sector": "Agro Chemicals"},
    {"symbol": "DEEPAKNTR", "name": "Deepak Nitrite Ltd", "sector": "Specialty Chemicals"},
    {"symbol": "TATACHEM", "name": "Tata Chemicals Ltd", "sector": "Chemicals"},
    {"symbol": "SRF", "name": "SRF Ltd", "sector": "Specialty Chemicals / Packaging"},
    {"symbol": "SOLARINDS", "name": "Solar Industries India Ltd", "sector": "Explosives / Defence"},
    {"symbol": "UPL", "name": "UPL Ltd", "sector": "Agro Chemicals"},
    {"symbol": "VOLTAS", "name": "Voltas Ltd", "sector": "Consumer Electronics / ACs"},
    {"symbol": "DIXON", "name": "Dixon Technologies (India) Ltd", "sector": "Electronics Manufacturing"},
    {"symbol": "BLUESTARCO", "name": "Blue Star Ltd", "sector": "Consumer Durables / ACs"},
    {"symbol": "KEI", "name": "KEI Industries Ltd", "sector": "Cables & Wires"},
    {"symbol": "PHOENIXLTD", "name": "The Phoenix Mills Ltd", "sector": "Real Estate / Malls"},
    {"symbol": "PRESTIGE", "name": "Prestige Estates Projects Ltd", "sector": "Real Estate"},
    {"symbol": "OBEROIRLTY", "name": "Oberoi Realty Ltd", "sector": "Real Estate"},
    {"symbol": "GODREJPROP", "name": "Godrej Properties Ltd", "sector": "Real Estate"},
    {"symbol": "LODHA", "name": "Macrotech Developers Ltd (Lodha)", "sector": "Real Estate"},
    {"symbol": "CONCOR", "name": "Container Corporation of India", "sector": "Logistics / Freight"},
    {"symbol": "DELHIVERY", "name": "Delhivery Ltd", "sector": "Logistics / Supply Chain"},
    {"symbol": "GMRAIRPORT", "name": "GMR Airports Infrastructure Ltd", "sector": "Airports / Infrastructure"},
    {"symbol": "IRCTC", "name": "Indian Railway Catering & Tourism", "sector": "Railway / Tourism"},
    {"symbol": "IRFC", "name": "Indian Railway Finance Corporation", "sector": "NBFC / Railways"},
    {"symbol": "RVNL", "name": "Rail Vikas Nigam Ltd", "sector": "Railway Infrastructure"},
    {"symbol": "MAZDOCK", "name": "Mazagon Dock Shipbuilders Ltd", "sector": "Defence / Shipbuilding"},
    {"symbol": "COCHINSHIP", "name": "Cochin Shipyard Ltd", "sector": "Defence / Shipbuilding"},
    {"symbol": "BDL", "name": "Bharat Dynamics Ltd", "sector": "Defence / Missiles"},
    {"symbol": "BHEL", "name": "Bharat Heavy Electricals Ltd", "sector": "Capital Goods / Power"},
    {"symbol": "NHPC", "name": "NHPC Ltd", "sector": "Hydro Power / Utilities"},
    {"symbol": "SJVN", "name": "SJVN Ltd", "sector": "Power Generation"},
    {"symbol": "TORNTPOWER", "name": "Torrent Power Ltd", "sector": "Power / Utilities"},
    {"symbol": "JSWENERGY", "name": "JSW Energy Ltd", "sector": "Power / Renewable"},
    {"symbol": "TATACOMM", "name": "Tata Communications Ltd", "sector": "Telecom / Cloud"},
    {"symbol": "INDUSTOWER", "name": "Indus Towers Ltd", "sector": "Telecom Infrastructure"},
    {"symbol": "NAUKRI", "name": "Info Edge (India) Ltd (Naukri)", "sector": "Internet / Recruitment"},
    {"symbol": "LTTS", "name": "L&T Technology Services Ltd", "sector": "ER&D / Engineering Tech"},
    {"symbol": "TATAELXSI", "name": "Tata Elxsi Ltd", "sector": "Design & Technology"},
    {"symbol": "MPHASIS", "name": "Mphasis Ltd", "sector": "Information Technology"},
    {"symbol": "COFORGE", "name": "Coforge Ltd", "sector": "Information Technology"},
    {"symbol": "KPITTECH", "name": "KPIT Technologies Ltd", "sector": "Automotive Software"},
    {"symbol": "OFSS", "name": "Oracle Financial Services Software", "sector": "FinTech / Software"},
    {"symbol": "CYIENT", "name": "Cyient Ltd", "sector": "Engineering / IT"},
    {"symbol": "SONATSOFTW", "name": "Sonata Software Ltd", "sector": "Information Technology"},
    {"symbol": "PAYTM", "name": "One97 Communications (Paytm)", "sector": "FinTech / Payments"},
    {"symbol": "NYKAA", "name": "FSN E-Commerce Ventures (Nykaa)", "sector": "E-Commerce / Beauty"},
    {"symbol": "KALYANKJIL", "name": "Kalyan Jewellers India Ltd", "sector": "Jewellery / Retail"},
    {"symbol": "JUBLFOOD", "name": "Jubilant FoodWorks Ltd (Domino's)", "sector": "QSR / Food Services"},
    {"symbol": "DEVYANI", "name": "Devyani International Ltd (KFC/PH)", "sector": "QSR / Food Services"},
    {"symbol": "RADICO", "name": "Radico Khaitan Ltd", "sector": "Beverages / AlcoBev"},
    {"symbol": "UNITDSPR", "name": "United Spirits Ltd (Diageo)", "sector": "Beverages / AlcoBev"},
    {"symbol": "MARICO", "name": "Marico Ltd", "sector": "FMCG / Edible Oils"},
    {"symbol": "EMAMILTD", "name": "Emami Ltd", "sector": "FMCG / Healthcare"},
    {"symbol": "BERGEPAINT", "name": "Berger Paints India Ltd", "sector": "Paints"},
    {"symbol": "PAGEIND", "name": "Page Industries Ltd (Jockey)", "sector": "Apparel / Textiles"},
    {"symbol": "ABCAPITAL", "name": "Aditya Birla Capital Ltd", "sector": "Financial Services"},
    {"symbol": "LTF", "name": "L&T Finance Ltd", "sector": "NBFC"},
    {"symbol": "MUTHOOTFIN", "name": "Muthoot Finance Ltd", "sector": "Gold Loan NBFC"},
    {"symbol": "MANAPPURAM", "name": "Manappuram Finance Ltd", "sector": "Gold Loan NBFC"},
    {"symbol": "POONAWALLA", "name": "Poonawalla Fincorp Ltd", "sector": "NBFC"},
    {"symbol": "SUNDARMFIN", "name": "Sundaram Finance Ltd", "sector": "Vehicle Financing / NBFC"},
    {"symbol": "GICRE", "name": "General Insurance Corp of India", "sector": "Reinsurance"},
    {"symbol": "NIACL", "name": "The New India Assurance Co Ltd", "sector": "General Insurance"},
    {"symbol": "ICICIPRULI", "name": "ICICI Prudential Life Insurance", "sector": "Insurance"},
    {"symbol": "ICICIGI", "name": "ICICI Lombard General Insurance", "sector": "General Insurance"},
    {"symbol": "STARHEALTH", "name": "Star Health & Allied Insurance", "sector": "Health Insurance"},
    {"symbol": "HDFCAMC", "name": "HDFC Asset Management Co Ltd", "sector": "Asset Management / AMC"},
    {"symbol": "NAM-INDIA", "name": "Nippon Life India Asset Management", "sector": "Asset Management / AMC"},
    {"symbol": "BSE", "name": "BSE Ltd (Bombay Stock Exchange)", "sector": "Exchange / Financial Market"},
    {"symbol": "CDSL", "name": "Central Depository Services (India)", "sector": "Depository Services"},
    {"symbol": "MCX", "name": "Multi Commodity Exchange of India", "sector": "Commodity Exchange"},
    {"symbol": "ANGELONE", "name": "Angel One Ltd", "sector": "Retail Broking / FinTech"},
    {"symbol": "KFINTECH", "name": "KFin Technologies Ltd", "sector": "FinTech / Registry"},
    {"symbol": "CAMS", "name": "Computer Age Management Services", "sector": "FinTech / Registrar"},
    {"symbol": "MOTILALOFS", "name": "Motilal Oswal Financial Services", "sector": "Broking / AMC"},
    {"symbol": "360ONE", "name": "360 ONE WAM Ltd (IIFL Wealth)", "sector": "Wealth Management"},
    {"symbol": "CRISIL", "name": "CRISIL Ltd", "sector": "Credit Rating / Analytics"},
    {"symbol": "IGL", "name": "Indraprastha Gas Ltd", "sector": "City Gas Distribution"},
    {"symbol": "MGL", "name": "Mahanagar Gas Ltd", "sector": "City Gas Distribution"},
    {"symbol": "PETRONET", "name": "Petronet LNG Ltd", "sector": "Gas Infrastructure / LNG"},
    {"symbol": "OIL", "name": "Oil India Ltd", "sector": "Oil Exploration"},
    {"symbol": "MRF", "name": "MRF Ltd", "sector": "Tyres"},
    {"symbol": "APOLLOTYRE", "name": "Apollo Tyres Ltd", "sector": "Tyres"},
    {"symbol": "BALKRISIND", "name": "Balkrishna Industries Ltd", "sector": "Off-Highway Tyres"},
    {"symbol": "UNOMINDA", "name": "Uno Minda Ltd", "sector": "Auto Ancillary / Lighting"},
    {"symbol": "SONACOMS", "name": "Sona BLW Precision Forgings Ltd", "sector": "Auto Components / EV"},
    {"symbol": "ENDURANCE", "name": "Endurance Technologies Ltd", "sector": "Auto Ancillary"},
    {"symbol": "EXIDEIND", "name": "Exide Industries Ltd", "sector": "Batteries / EV"},
    {"symbol": "ARE&M", "name": "Amara Raja Energy & Mobility Ltd", "sector": "Batteries / EV"},
    {"symbol": "MOTHERSON", "name": "Samvardhana Motherson International", "sector": "Auto Ancillary / Wiring"},
    {"symbol": "ESCORTS", "name": "Escorts Kubota Ltd", "sector": "Tractors / Agri Machinery"},
    {"symbol": "ASHOKLEY", "name": "Ashok Leyland Ltd", "sector": "Commercial Vehicles"},
    {"symbol": "BHARATFORG", "name": "Bharat Forge Ltd", "sector": "Forging / Defence / Auto"},
    {"symbol": "SCHAEFFLER", "name": "Schaeffler India Ltd", "sector": "Bearings / Precision"},
    {"symbol": "SKFINDIA", "name": "SKF India Ltd", "sector": "Bearings / Industrial"},
    {"symbol": "THERMAX", "name": "Thermax Ltd", "sector": "Energy & Environment Tech"},
    {"symbol": "KEC", "name": "KEC International Ltd", "sector": "Power T&D / Infrastructure"},
    {"symbol": "KPIL", "name": "Kalpataru Projects International", "sector": "Power T&D / Infra"},
    {"symbol": "NCC", "name": "NCC Ltd", "sector": "Construction / Infra"},
    {"symbol": "NBCC", "name": "NBCC (India) Ltd", "sector": "Construction / Real Estate"},
    {"symbol": "HUDCO", "name": "Housing & Urban Development Corp", "sector": "Housing Finance / Infra"},
    {"symbol": "TATAINVEST", "name": "Tata Investment Corporation Ltd", "sector": "Investment / Holding"},
    {"symbol": "JSL", "name": "Jindal Stainless Ltd", "sector": "Stainless Steel"},
    {"symbol": "APLAPOLLO", "name": "APL Apollo Tubes Ltd", "sector": "Steel Pipes & Tubes"},
    {"symbol": "FLUOROCHEM", "name": "Gujarat Fluorochemicals Ltd", "sector": "Fluorochemicals"},
    {"symbol": "AARTIIND", "name": "Aarti Industries Ltd", "sector": "Specialty Chemicals"},
    {"symbol": "ATUL", "name": "Atul Ltd", "sector": "Specialty Chemicals"},
    {"symbol": "COROMANDEL", "name": "Coromandel International Ltd", "sector": "Fertilizers / Agri"},
    {"symbol": "CHAMBLFERT", "name": "Chambal Fertilisers and Chemicals", "sector": "Fertilizers"},
    {"symbol": "FACT", "name": "Fertilisers & Chemicals Travancore", "sector": "Fertilizers / Chemicals"},
    {"symbol": "SUMICHEM", "name": "Sumitomo Chemical India Ltd", "sector": "Agro Chemicals"},

    # =====================================================================
    # MOMENTUM UNIVERSE — High Beta / Relative Strength Leaders (NSE)
    # Proven outperformers: defence, electronics, railways, clean energy,
    # specialty mid-caps with institutional accumulation & volume surges.
    # =====================================================================

    # Defence & Aerospace Momentum
    {"symbol": "PARAS", "name": "Paras Defence and Space Technologies", "sector": "Defence / Space"},
    {"symbol": "DATAPATTNS", "name": "Data Patterns (India) Ltd", "sector": "Defence Electronics"},
    {"symbol": "MTAR", "name": "MTAR Technologies Ltd", "sector": "Defence / Aerospace Precision"},
    {"symbol": "IDEAFORGE", "name": "ideaForge Technology Ltd", "sector": "Defence Drones / UAV"},
    {"symbol": "PREMIEREXP", "name": "Premier Explosives Ltd", "sector": "Defence / Explosives"},

    # Electronics & PLI Momentum
    {"symbol": "KAYNES", "name": "Kaynes Technology India Ltd", "sector": "Electronics Manufacturing / IoT"},
    {"symbol": "SYRMA", "name": "Syrma SGS Technology Ltd", "sector": "Electronics Manufacturing"},
    {"symbol": "AVALON", "name": "Avalon Technologies Ltd", "sector": "Electronics Manufacturing"},
    {"symbol": "AMBER", "name": "Amber Enterprises India Ltd", "sector": "Consumer Electronics / PLI"},
    {"symbol": "IDEAFORGE", "name": "ideaForge Technology Ltd", "sector": "Defence Drones / UAV"},

    # Railways & Infra Momentum
    {"symbol": "RAILTEL", "name": "RailTel Corporation of India Ltd", "sector": "Railways / Telecom Infra"},
    {"symbol": "TITAGARH", "name": "Titagarh Rail Systems Ltd", "sector": "Railway Wagons"},
    {"symbol": "TEXRAIL", "name": "Texmaco Rail & Engineering Ltd", "sector": "Railway Engineering"},
    {"symbol": "IRCON", "name": "Ircon International Ltd", "sector": "Railway Construction"},
    {"symbol": "HFCL", "name": "HFCL Ltd", "sector": "Fibre Optics / Infra"},

    # Green Energy / Renewable Momentum
    {"symbol": "IREDA", "name": "Indian Renewable Energy Development Agency", "sector": "Green Finance / Renewable"},
    {"symbol": "INOXGREEN", "name": "Inox Green Energy Services Ltd", "sector": "Wind Energy / O&M"},
    {"symbol": "BFUTILITIE", "name": "BF Utilities Ltd", "sector": "Power / Renewable"},
    {"symbol": "GREENPANEL", "name": "Greenpanel Industries Ltd", "sector": "MDF / Green Building"},
    {"symbol": "WAAREEENER", "name": "Waaree Energies Ltd", "sector": "Solar Manufacturing"},

    # Specialty Chemicals Momentum
    {"symbol": "FINEORG", "name": "Fine Organic Industries Ltd", "sector": "Specialty Oleo Chemicals"},
    {"symbol": "GALAXYSURF", "name": "Galaxy Surfactants Ltd", "sector": "Surfactants / Specialty Chem"},
    {"symbol": "EPIGRAL", "name": "Epigral Ltd", "sector": "Chloro Chemicals"},
    {"symbol": "ANUPAMRASI", "name": "Anupam Rasayan India Ltd", "sector": "CSM / Agro Chemicals"},

    # FinTech & Digital Momentum
    {"symbol": "INDIAMART", "name": "IndiaMART InterMESH Ltd", "sector": "B2B E-Commerce / SaaS"},
    {"symbol": "TARSONS", "name": "Tarsons Products Ltd", "sector": "Lab Consumables / Life Sciences"},
    {"symbol": "KRSNAA", "name": "Krsnaa Diagnostics Ltd", "sector": "Healthcare / Diagnostics"},
    {"symbol": "PGHH", "name": "Procter & Gamble Hygiene", "sector": "FMCG / Healthcare"},

    # Capital Goods / Power Equipment Momentum
    {"symbol": "VOLTAMP", "name": "Voltamp Transformers Ltd", "sector": "Transformers / Power Equip"},
    {"symbol": "GPIL", "name": "Godawari Power and Ispat Ltd", "sector": "Steel / Power"},
    {"symbol": "PRAJIND", "name": "Praj Industries Ltd", "sector": "Bio-energy / Ethanol / Water"},
    {"symbol": "ELECON", "name": "Elecon Engineering Company Ltd", "sector": "Industrial Gears / Materials"},
    {"symbol": "KENNAMETAL", "name": "Kennametal India Ltd", "sector": "Cutting Tools / Engineering"},

    # Housing Finance Momentum
    {"symbol": "AAVAS", "name": "Aavas Financiers Ltd", "sector": "Affordable Housing Finance"},
    {"symbol": "HOMEFIRST", "name": "Home First Finance Company", "sector": "Housing Finance / NBFC"},
    {"symbol": "APTUS", "name": "Aptus Value Housing Finance", "sector": "Housing Finance / NBFC"},
    {"symbol": "PNBHOUSING", "name": "PNB Housing Finance Ltd", "sector": "Housing Finance"},

    # Consumer & Retail Momentum
    {"symbol": "CAMPUS", "name": "Campus Activewear Ltd", "sector": "Sports Footwear / Retail"},
    {"symbol": "SAPPHIRE", "name": "Sapphire Foods India Ltd (KFC/PH)", "sector": "QSR / Consumer"},
    {"symbol": "GODIGIT", "name": "Go Digit General Insurance Ltd", "sector": "InsurTech / General Insurance"},
]

# Use full Nifty 500 universe when available
if MASTER_NSE_UNIVERSE and len(MASTER_NSE_UNIVERSE) >= 500:
    LIQUID_UNIVERSE = MASTER_NSE_UNIVERSE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def calculate_supertrend(df: pd.DataFrame, period: int = 10, factor: float = 3.0) -> pd.DataFrame:
    """
    Standard TradingView Supertrend (pd=10, factor=3)
    Direction: 1 = Bullish (Green), -1 = Bearish (Red)
    """
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)
    
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Wilder's Smoothing / RMA for ATR
    atr = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    
    hl2 = (high + low) / 2.0
    upper_band = hl2 + (factor * atr)
    lower_band = hl2 - (factor * atr)
    
    ub = upper_band.to_numpy().copy()
    lb = lower_band.to_numpy().copy()
    cl = close.to_numpy()
    
    st = np.zeros(len(df))
    direction = np.ones(len(df), dtype=int)
    
    for i in range(1, len(df)):
        if cl[i-1] <= ub[i-1]:
            ub[i] = min(ub[i], ub[i-1])
        if cl[i-1] >= lb[i-1]:
            lb[i] = max(lb[i], lb[i-1])
            
        if direction[i-1] == 1:
            if cl[i] < lb[i]:
                direction[i] = -1
                st[i] = ub[i]
            else:
                direction[i] = 1
                st[i] = lb[i]
        else:
            if cl[i] > ub[i]:
                direction[i] = 1
                st[i] = lb[i]
            else:
                direction[i] = -1
                st[i] = ub[i]
                
    df['supertrend'] = st
    df['st_dir'] = direction
    df['atr'] = atr
    return df

# ==============================================================================
# HIGH-RESILIENCE HTTP SESSION & MULTI-TIER OHLCV CACHING ENGINE
# ==============================================================================
_HTTP_SESSION = requests.Session()
_HTTP_ADAPTER = HTTPAdapter(pool_connections=50, pool_maxsize=100, max_retries=1)
_HTTP_SESSION.mount("https://", _HTTP_ADAPTER)
_HTTP_SESSION.mount("http://", _HTTP_ADAPTER)

CACHE_OHLCV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "ohlcv")
os.makedirs(CACHE_OHLCV_DIR, exist_ok=True)
_OHLCV_MEM_CACHE = {}  # key -> (df, timestamp)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
]

def _build_dataframe_from_dict(d: dict, range_str: str, interval: str) -> pd.DataFrame:
    """Builds and computes full technical indicators on OHLCV dictionary."""
    try:
        timestamps = d.get("timestamp", [])
        if not timestamps:
            return pd.DataFrame()
        df = pd.DataFrame({
            "timestamp": timestamps,
            "date": pd.to_datetime(timestamps, unit="s"),
            "open": d.get("open", []),
            "high": d.get("high", []),
            "low": d.get("low", []),
            "close": d.get("close", []),
            "volume": d.get("volume", [])
        }).dropna().reset_index(drop=True)
        
        min_bars = 40 if "200" in range_str or interval in ["15m", "5m"] else 15
        if len(df) < min_bars:
            return pd.DataFrame()
            
        # ── Core Trend Indicators ──────────────────────────────────────────
        df["ema50"]     = df["close"].ewm(span=50,  adjust=False).mean()
        df["ema200"]    = df["close"].ewm(span=200, adjust=False).mean()
        df["ema20"]     = df["close"].ewm(span=20,  adjust=False).mean()
        df["vol_sma20"] = df["volume"].rolling(20).mean()
        
        # ── RSI-14 (Wilder's smoothing) ────────────────────────────────────
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / (loss + 1e-9)
        df["rsi14"] = 100.0 - (100.0 / (1.0 + rs))
        
        # ── Supertrend (10, 3) ─────────────────────────────────────────────
        calculate_supertrend(df, period=10, factor=3.0)
        
        # ── ADX-14 (Wilder's DMI) — Trend Strength Guard ──────────────────
        h         = df["high"]
        l         = df["low"]
        ph        = h.shift(1)
        pl        = l.shift(1)
        up_mv     = h - ph
        dn_mv     = pl - l
        plus_dm   = np.where((up_mv > dn_mv) & (up_mv > 0), up_mv, 0.0)
        minus_dm  = np.where((dn_mv > up_mv) & (dn_mv > 0), dn_mv, 0.0)
        atr14     = df["atr"]
        plus_di   = 100 * pd.Series(plus_dm,  index=df.index).ewm(alpha=1/14, adjust=False).mean() / (atr14 + 1e-9)
        minus_di  = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / (atr14 + 1e-9)
        dx        = (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)) * 100
        df["adx14"]    = dx.ewm(alpha=1/14, adjust=False).mean()
        df["plus_di"]  = plus_di
        df["minus_di"] = minus_di
        
        # ── MACD (12, 26, 9) — Momentum Confirmation ──────────────────────
        ema12             = df["close"].ewm(span=12, adjust=False).mean()
        ema26             = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"]        = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"]   = df["macd"] - df["macd_signal"]
        
        # ── 52-Week High / Low — Proximity to Breakout Zone ───────────────
        w52 = min(252, len(df))
        df["high_52w"]          = df["high"].rolling(w52).max()
        df["low_52w"]           = df["low"].rolling(w52).min()
        df["pct_from_52w_high"] = ((df["high_52w"] - df["close"]) / (df["high_52w"] + 1e-9)) * 100.0
        
        # ── Rate of Change (ROC) — Relative Momentum Score ────────────────
        df["roc20"] = df["close"].pct_change(20) * 100.0
        df["roc60"] = df["close"].pct_change(60) * 100.0
        
        return df
    except Exception:
        return pd.DataFrame()

def fetch_stock_data(symbol: str, range_str: str = "1y", interval: str = "1d", force_network: bool = False) -> pd.DataFrame:
    """
    Fetch OHLCV from Yahoo Finance v8 API with multi-tier caching and resilience:
    1. In-memory hot cache (TTL: 10m for Daily, 60s for Intraday)
    2. Connection-pooled HTTP with retry across query1 and query2 endpoints
    3. Persistent disk cache fallback if network times out or Yahoo throttles
    """
    clean = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    ALIAS_MAP = {
        "LTIM": "LTM",
        "LTIMINDTREE": "LTM",
        "HDFC": "HDFCBANK",
        "HUL": "HINDUNILVR",
        "BOB": "BANKBARODA",
        "ICICILOMBARD": "ICICIGI",
        "SBICARDS": "SBICARD",
        "BAJAJ-AUTO": "BAJAJ-AUTO",
        "BAJAJAUTO": "BAJAJ-AUTO",
        "TATAMOTORS": "TATAMOTORS",
        "TATAMOTOR": "TATAMOTORS",
        "M&M": "M&M",
        "MM": "M&M",
        "BAJAJFINANCE": "BAJFINANCE",
        "BAJAJFINSERV": "BAJAJFINSV",
        "NESTLE": "NESTLEIND",
        "L&T": "LT",
        "LARSEN": "LT",
        "MCDOWELL": "MCDOWELL-N",
        "UNITEDSPIRITS": "MCDOWELL-N",
        "DUMMYHEG": "HEG"
    }
    resolved = ALIAS_MAP.get(clean, clean)
    cache_key = f"{resolved}_{range_str}_{interval}"
    now_ts = time.time()
    
    # Tier 1: In-Memory Hot Cache
    ttl = 60.0 if interval in ["15m", "5m"] else 600.0
    if not force_network and cache_key in _OHLCV_MEM_CACHE:
        cached_df, cached_time = _OHLCV_MEM_CACHE[cache_key]
        if (now_ts - cached_time) < ttl:
            return cached_df.copy()
            
    # Tier 2: Live Network Fetch across NSE (.NS) and fallback to BSE (.BO) with Dual Host Redundancy
    ticker_variants = [f"{resolved}.NS", f"{resolved}.BO"]
    raw_payload = None
    
    for ticker in ticker_variants:
        endpoints = [
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={range_str}&interval={interval}",
            f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?range={range_str}&interval={interval}"
        ]
        for url in endpoints:
            for attempt in range(2):
                try:
                    headers = {
                        "User-Agent": USER_AGENTS[(abs(hash(clean)) + attempt) % len(USER_AGENTS)],
                        "Accept": "application/json"
                    }
                    resp = _HTTP_SESSION.get(url, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        if "chart" in data and "result" in data["chart"] and data["chart"]["result"]:
                            res_entry = data["chart"]["result"][0]
                            if res_entry.get("timestamp") and len(res_entry.get("timestamp")) > 0:
                                raw_payload = res_entry
                                break
                    elif resp.status_code == 429:
                        time.sleep(0.25)
                except Exception:
                    time.sleep(0.15)
            if raw_payload:
                break
        if raw_payload:
            break
            
    # Tier 3: Process Network Success & Update Persistent Disk Cache
    disk_path = os.path.join(CACHE_OHLCV_DIR, f"{cache_key}.json")
    if raw_payload:
        timestamps = raw_payload.get("timestamp", [])
        indicators = raw_payload.get("indicators", {}).get("quote", [{}])[0]
        cache_dict = {
            "timestamp": timestamps,
            "open": indicators.get("open", []),
            "high": indicators.get("high", []),
            "low": indicators.get("low", []),
            "close": indicators.get("close", []),
            "volume": indicators.get("volume", [])
        }
        df = _build_dataframe_from_dict(cache_dict, range_str, interval)
        if not df.empty:
            try:
                with open(disk_path, "w", encoding="utf-8") as f:
                    json.dump(cache_dict, f)
            except Exception:
                pass
            _OHLCV_MEM_CACHE[cache_key] = (df, now_ts)
            return df.copy()

    # Tier 4: Fallback to Persistent Disk Cache (ensures data ALWAYS loads even during network hiccup / rate limit)
    if os.path.exists(disk_path):
        try:
            with open(disk_path, "r", encoding="utf-8") as f:
                disk_dict = json.load(f)
            df = _build_dataframe_from_dict(disk_dict, range_str, interval)
            if not df.empty:
                _OHLCV_MEM_CACHE[cache_key] = (df, now_ts)
                return df.copy()
        except Exception:
            pass

    # Tier 5: Fallback to existing memory cache even if expired
    if cache_key in _OHLCV_MEM_CACHE:
        return _OHLCV_MEM_CACHE[cache_key][0].copy()
        
    return pd.DataFrame()

# ==============================================================================
# SECTION 1: DAILY SWING TRADING STRATEGY  [PRO EDITION v2]
# Base: Daily 50 EMA + Supertrend (10, 3)
# Pro Filters: ADX-14 | MACD | RSI 50-65 | Volume Surge | 200 EMA | ROC | 52W
# Accuracy target: 40-55% win rate with 2.5:1+ payoff.
# ==============================================================================
def analyze_daily_stock(item: dict, days_lookback: int = 14) -> list:
    symbol = item["symbol"]
    name   = item["name"]
    sector = item["sector"]
    
    df = fetch_stock_data(symbol, range_str="1y", interval="1d")
    if df.empty or len(df) < 65:
        return []
        
    # Base signal triggers (EMA50 crossover with Supertrend direction)
    df["is_buy"]  = (df["close"] > df["ema50"]) & (df["st_dir"] == 1)
    df["is_sell"] = (df["close"] < df["ema50"]) & (df["st_dir"] == -1)
    
    prev_buy  = df["is_buy"].shift(1).fillna(False).astype(bool)
    prev_sell = df["is_sell"].shift(1).fillna(False).astype(bool)
    
    df["buy_trigger"]  = df["is_buy"]  & (~prev_buy)
    df["sell_trigger"] = df["is_sell"] & (~prev_sell)
    
    total_bars  = len(df)
    scan_window = min(days_lookback, total_bars - 60)
    
    # ── Current Market Snapshot ────────────────────────────────────────────
    curr_close    = float(df["close"].iloc[-1])
    curr_ema50    = float(df["ema50"].iloc[-1])
    curr_ema200   = float(df["ema200"].iloc[-1])
    curr_st       = float(df["supertrend"].iloc[-1])
    curr_st_dir   = int(df["st_dir"].iloc[-1])
    curr_rsi      = float(df["rsi14"].iloc[-1])
    curr_atr      = float(df["atr"].iloc[-1])
    curr_adx      = float(df["adx14"].iloc[-1]) if not pd.isna(df["adx14"].iloc[-1]) else 0.0
    curr_macd_h   = float(df["macd_hist"].iloc[-1]) if not pd.isna(df["macd_hist"].iloc[-1]) else 0.0
    curr_vol      = float(df["volume"].iloc[-1])
    curr_vol_ma   = float(df["vol_sma20"].iloc[-1]) if not pd.isna(df["vol_sma20"].iloc[-1]) else curr_vol
    vol_ratio     = curr_vol / (curr_vol_ma + 1e-9)
    curr_52w_gap  = float(df["pct_from_52w_high"].iloc[-1]) if not pd.isna(df["pct_from_52w_high"].iloc[-1]) else 99.0
    curr_roc20    = float(df["roc20"].iloc[-1]) if not pd.isna(df["roc20"].iloc[-1]) else 0.0
    curr_roc60    = float(df["roc60"].iloc[-1]) if not pd.isna(df["roc60"].iloc[-1]) else 0.0
    
    detected_signals = []
    
    for i in range(total_bars - scan_window, total_bars):
        days_ago = (total_bars - 1) - i
        b_trig   = bool(df["buy_trigger"].iloc[i])
        s_trig   = bool(df["sell_trigger"].iloc[i])
        
        if not (b_trig or s_trig):
            continue
            
        sig_type      = "BUY" if b_trig else "SELL"
        trig_date     = df["date"].iloc[i].strftime("%d-%b-%Y")
        trig_close    = float(df["close"].iloc[i])
        trig_vol      = float(df["volume"].iloc[i])
        trig_vol_ma   = float(df["vol_sma20"].iloc[i]) if not pd.isna(df["vol_sma20"].iloc[i]) else trig_vol
        trig_vol_ratio = trig_vol / (trig_vol_ma + 1e-9)
        trig_rsi      = float(df["rsi14"].iloc[i])
        trig_adx      = float(df["adx14"].iloc[i]) if not pd.isna(df["adx14"].iloc[i]) else 0.0
        trig_macd_h   = float(df["macd_hist"].iloc[i]) if not pd.isna(df["macd_hist"].iloc[i]) else 0.0
        trig_roc20    = float(df["roc20"].iloc[i]) if not pd.isna(df["roc20"].iloc[i]) else 0.0
        trig_roc60    = float(df["roc60"].iloc[i]) if not pd.isna(df["roc60"].iloc[i]) else 0.0
        trig_52w_gap  = float(df["pct_from_52w_high"].iloc[i]) if not pd.isna(df["pct_from_52w_high"].iloc[i]) else 99.0
        
        pct_from_trigger = ((curr_close - trig_close) / trig_close) * 100.0
        pct_from_ema50   = ((curr_close - curr_ema50) / curr_ema50) * 100.0
        
        # ══════════════════════════════════════════════════════════════════
        #  PRO FILTER SUITE — 7 Mathematical Conditions (each scored 0/1)
        #  Confidence Score 5-7 = ELITE | 3-4 = STANDARD | <3 = AVOID
        # ══════════════════════════════════════════════════════════════════
        if sig_type == "BUY":
            # F1: ADX ≥ 20 → confirmed uptrend, not just noise
            f1_adx_trend     = trig_adx >= 20.0
            # F2: 200 EMA long-term alignment → only buy in bull market
            f2_bull_market   = (curr_close > curr_ema200) and (curr_ema50 > curr_ema200)
            # F3: RSI tightened to 50-65 → momentum without overbought risk
            f3_rsi_zone      = 50.0 <= trig_rsi <= 65.0
            # F4: Volume surge ≥ 1.2× avg → institutional conviction on entry
            f4_vol_surge     = trig_vol_ratio >= 1.20
            # F5: MACD histogram positive → rising momentum
            f5_macd_bull     = trig_macd_h > 0
            # F6: Positive momentum score → stock outperforming market
            f6_momentum      = (trig_roc20 > 0) and (trig_roc60 > 0)
            # F7: Within 20% of 52-week high → momentum leader, not laggard
            f7_near_highs    = trig_52w_gap <= 20.0
            
            pro_filters = [f1_adx_trend, f2_bull_market, f3_rsi_zone, f4_vol_surge, f5_macd_bull, f6_momentum, f7_near_highs]
            confidence_score = sum(pro_filters)
            
            # Legacy enhanced_score (kept for display compatibility)
            trend_aligned = f2_bull_market
            vol_confirmed = f4_vol_surge
            rsi_healthy   = f3_rsi_zone
            
        else:  # SELL / SHORT
            # F1: ADX ≥ 20 → confirmed downtrend
            f1_adx_trend   = trig_adx >= 20.0
            # F2: 200 EMA bear-market alignment → only short below 200 EMA
            f2_bear_market = curr_close < curr_ema200
            # F3: RSI ≤ 48 → bearish momentum without oversold risk
            f3_rsi_zone    = trig_rsi <= 48.0
            # F4: Volume on breakdown ≥ 1.2×
            f4_vol_surge   = trig_vol_ratio >= 1.20
            # F5: MACD histogram negative → declining momentum
            f5_macd_bear   = trig_macd_h < 0
            # F6: Negative ROC → underperforming market
            f6_momentum    = trig_roc20 < 0
            # F7: Within 35% of 52-week LOW (near lows = weak, ideal for shorts)
            low_52w        = float(df["low_52w"].iloc[i]) if not pd.isna(df["low_52w"].iloc[i]) else curr_close
            f7_near_lows   = curr_close <= (low_52w * 1.35)
            
            pro_filters = [f1_adx_trend, f2_bear_market, f3_rsi_zone, f4_vol_surge, f5_macd_bear, f6_momentum, f7_near_lows]
            confidence_score = sum(pro_filters)
            
            trend_aligned = f2_bear_market
            vol_confirmed = f4_vol_surge
            rsi_healthy   = f3_rsi_zone
        
        enhanced_score = sum([trend_aligned, vol_confirmed, rsi_healthy])
        
        # ── Confidence Label ───────────────────────────────────────────────
        if confidence_score >= 6:
            confidence_label = "ELITE (6-7/7)"
            confidence_badge = "elite"
        elif confidence_score >= 4:
            confidence_label = "HIGH (4-5/7)"
            confidence_badge = "high"
        elif confidence_score >= 2:
            confidence_label = "STANDARD (2-3/7)"
            confidence_badge = "standard"
        else:
            confidence_label = "LOW (<2/7) — SKIP"
            confidence_badge = "low"
        
        # ── Suitability & Risk/Reward ──────────────────────────────────────
        suitability_verdict = "ACTIONABLE"
        verdict_badge       = "success"
        reasons             = []
        action_plan         = ""
        
        if sig_type == "BUY":
            stop_loss      = round(min(curr_st, curr_ema50 - 0.5 * curr_atr), 2)
            risk_per_share = max(curr_close - stop_loss, 0.01)
            risk_pct       = (risk_per_share / curr_close) * 100.0
            target1        = round(curr_close + 1.5 * risk_per_share, 2)
            target2        = round(curr_close + 2.5 * risk_per_share, 2)
            target3        = round(curr_close + 4.0 * risk_per_share, 2)   # 4R extended target
            
            if curr_close < curr_ema50 or curr_st_dir == -1:
                suitability_verdict = "NOT SUITABLE (INVALIDATED)"
                verdict_badge = "danger"
                reasons.append("Breakdown: Price dropped back below 50 EMA or Supertrend flipped red.")
                action_plan = "Do NOT Enter. The bullish setup has failed; wait for a fresh reset."
            elif pct_from_trigger > 4.2:
                suitability_verdict = "NOT SUITABLE (OVEREXTENDED)"
                verdict_badge = "warning"
                reasons.append(f"Chasing Risk: Price surged +{pct_from_trigger:.1f}% from trigger close. High mean-reversion risk.")
                action_plan = f"Wait for pullback to EMA50 support (around ₹{curr_ema50:.2f}) before entering."
            elif risk_pct > 6.0:
                suitability_verdict = "NOT SUITABLE (RISK TOO WIDE)"
                verdict_badge = "warning"
                reasons.append(f"Poor R/R: Stop-Loss is {risk_pct:.1f}% away from current price (>6% max limit).")
                action_plan = f"Wait for price to consolidate closer to SL (₹{stop_loss:.2f}) to reduce risk."
            elif days_ago >= 5 and pct_from_trigger > 2.5:
                suitability_verdict = "NOT SUITABLE (STALE SETUP)"
                verdict_badge = "secondary"
                reasons.append(f"Stale: Triggered {days_ago} trading days ago; primary breakout impulse already spent.")
                action_plan = "Keep on watchlist for re-test or fresh consolidation breakout."
            elif confidence_score < 2:
                suitability_verdict = "LOW CONFIDENCE — SKIP"
                verdict_badge = "secondary"
                reasons.append(f"Only {confidence_score}/7 pro filters passed. High probability of false breakout.")
                action_plan = "Skip this signal. Wait for a setup with 4+ filters confirmed."
            else:
                suitability_verdict = "ACTIONABLE ENTRY (READY NOW)"
                verdict_badge = "success"
                if days_ago == 0:
                    reasons.append("Fresh Trigger TODAY: Real-time breakout momentum!")
                elif days_ago <= 2:
                    reasons.append(f"Prime Entry Window: Triggered {days_ago} day(s) ago — optimal buffer (+{pct_from_trigger:.1f}%).")
                else:
                    reasons.append(f"Pullback Retest: Holding safely above 50 EMA support (+{pct_from_ema50:.1f}%).")
                reasons.append(f"Risk: {risk_pct:.1f}% to SL ₹{stop_loss:.2f} | Confidence: {confidence_score}/7 filters ✓")
                if not f1_adx_trend:
                    reasons.append("⚠ ADX < 20: Trend strength is weak. Reduce position size by 50%.")
                if not f6_momentum:
                    reasons.append("⚠ ROC negative: Stock not outperforming market — consider skipping.")
                action_plan = (f"Actionable Buy: Enter at CMP ₹{curr_close:.2f}. "
                               f"SL: ₹{stop_loss:.2f} | T1: ₹{target1:.2f} (1.5R) | T2: ₹{target2:.2f} (2.5R) | T3: ₹{target3:.2f} (4R extended). "
                               f"Risk ₹{risk_per_share:.2f}/share. Use 1% capital risk rule.")
                
        else:  # SELL / SHORT
            stop_loss      = round(max(curr_st, curr_ema50 + 0.5 * curr_atr), 2)
            risk_per_share = max(stop_loss - curr_close, 0.01)
            risk_pct       = (risk_per_share / curr_close) * 100.0
            target1        = round(curr_close - 1.5 * risk_per_share, 2)
            target2        = round(curr_close - 2.5 * risk_per_share, 2)
            target3        = round(curr_close - 4.0 * risk_per_share, 2)   # 4R extended
            
            if curr_close > curr_ema50 or curr_st_dir == 1:
                suitability_verdict = "NOT SUITABLE (INVALIDATED)"
                verdict_badge = "danger"
                reasons.append("Breakout: Price crossed back above 50 EMA / Supertrend flipped green.")
                action_plan = "Do NOT Short. Bearish setup is invalidated."
            elif pct_from_trigger < -4.5:
                suitability_verdict = "NOT SUITABLE (OVEREXTENDED SELL)"
                verdict_badge = "warning"
                reasons.append(f"Over-dumped: Price plunged {pct_from_trigger:.1f}% from breakdown; short-covering risk is high.")
                action_plan = "Avoid aggressive shorts; wait for pullback to 50 EMA resistance."
            elif risk_pct > 6.0:
                suitability_verdict = "NOT SUITABLE (RISK TOO WIDE)"
                verdict_badge = "warning"
                reasons.append(f"Wide SL: Stop-Loss is {risk_pct:.1f}% above current price.")
                action_plan = "Risk exceeds standard capital risk tolerance."
            elif confidence_score < 2:
                suitability_verdict = "LOW CONFIDENCE — SKIP"
                verdict_badge = "secondary"
                reasons.append(f"Only {confidence_score}/7 pro filters passed. High probability of failed breakdown.")
                action_plan = "Skip this signal. Wait for a setup with 4+ filters confirmed."
            else:
                suitability_verdict = "ACTIONABLE SHORT / EXIT LONGS"
                verdict_badge = "danger"
                reasons.append(f"Active Breakdown: Triggered {days_ago} day(s) ago; bearish trend intact.")
                reasons.append(f"Risk: {risk_pct:.1f}% to SL ₹{stop_loss:.2f} | Confidence: {confidence_score}/7 filters ✓")
                action_plan = (f"Exit longs or initiate short at ₹{curr_close:.2f}. "
                               f"SL: ₹{stop_loss:.2f} | T1: ₹{target1:.2f} (1.5R) | T2: ₹{target2:.2f} (2.5R).")

        detected_signals.append({
            "mode":          "daily",
            "symbol":        symbol,
            "name":          name,
            "sector":        sector,
            "timeframe":     "Daily",
            "strategy_name": "Daily 50 EMA + Supertrend + ADX + MACD + ROC [Pro v2]",
            "signal_type":   sig_type,
            "trigger_date":  trig_date,
            "days_ago":      days_ago,
            "trigger_price": round(trig_close, 2),
            "current_price": round(curr_close, 2),
            "main_ema":      round(curr_ema50, 2),
            "main_ema_name": "50 EMA",
            "ema200":        round(curr_ema200, 2),
            "supertrend":    round(curr_st, 2),
            "supertrend_direction": "Bullish (Green)" if curr_st_dir == 1 else "Bearish (Red)",
            "atr":           round(curr_atr, 2),
            "rsi14":         round(curr_rsi, 1),
            "adx14":         round(curr_adx, 1),
            "macd_hist":     round(curr_macd_h, 3),
            "roc20":         round(curr_roc20, 2),
            "roc60":         round(curr_roc60, 2),
            "pct_from_52w_high": round(curr_52w_gap, 1),
            "volume_ratio":  round(vol_ratio, 2),
            "pct_from_trigger": round(pct_from_trigger, 2),
            "pct_from_ema":  round(pct_from_ema50, 2),
            "stop_loss":     stop_loss,
            "risk_pct":      round(risk_pct, 2),
            "target1":       target1,
            "target2":       target2,
            "target3":       target3,
            "reward_risk_ratio": "1:1.5 (T1) / 1:2.5 (T2) / 1:4 (T3)",
            "suitability":   suitability_verdict,
            "verdict_badge": verdict_badge,
            "is_actionable": "ACTIONABLE" in suitability_verdict,
            "reasons":       reasons,
            "action_plan":   action_plan,
            "confidence_score": confidence_score,
            "confidence_label": confidence_label,
            "confidence_badge": confidence_badge,
            "enhanced_option": {
                "trend_aligned": bool(trend_aligned),
                "vol_confirmed": bool(vol_confirmed),
                "rsi_healthy":   bool(rsi_healthy),
                "adx_trending":  bool(f1_adx_trend),
                "macd_bullish":  bool(f5_macd_bull if sig_type == "BUY" else f5_macd_bear),
                "momentum_ok":   bool(f6_momentum),
                "near_highs":    bool(f7_near_highs if sig_type == "BUY" else f7_near_lows),
                "pro_score":     f"{confidence_score}/7",
                "pro_status":    confidence_label
            }
        })
        
    return detected_signals


# ==============================================================================
# SECTION 2: INTRADAY MOMENTUM STRATEGY
# Criteria: 15-Minute Timeframe | 200 EMA | Supertrend (10, 3) | Live Session Scan
# ==============================================================================
def analyze_intraday_stock(item: dict, bars_lookback: int = 25, interval: str = "15m") -> list:
    """
    Intraday Strategy using 200 EMA + Supertrend (10, 3) on 15m candles.
    1 trading day = 25 bars of 15-minutes (9:15 AM to 3:30 PM IST).
    """
    symbol = item["symbol"]
    name = item["name"]
    sector = item["sector"]
    
    df = fetch_stock_data(symbol, range_str="1mo", interval=interval)
    if df.empty or len(df) < 220:
        return []
        
    # Intraday Signal Rules:
    # BUY: Intraday Close > 200 EMA AND Supertrend == Bullish (1)
    # SELL: Intraday Close < 200 EMA AND Supertrend == Bearish (-1)
    df["is_buy"] = (df["close"] > df["ema200"]) & (df["st_dir"] == 1)
    df["is_sell"] = (df["close"] < df["ema200"]) & (df["st_dir"] == -1)
    
    prev_buy = df["is_buy"].shift(1).fillna(False).astype(bool)
    prev_sell = df["is_sell"].shift(1).fillna(False).astype(bool)
    
    df["buy_trigger"] = df["is_buy"] & (~prev_buy)
    df["sell_trigger"] = df["is_sell"] & (~prev_sell)
    
    total_bars = len(df)
    scan_window = min(bars_lookback, total_bars - 200)
    
    curr_close = float(df["close"].iloc[-1])
    curr_ema200 = float(df["ema200"].iloc[-1])
    curr_st = float(df["supertrend"].iloc[-1])
    curr_st_dir = int(df["st_dir"].iloc[-1])
    curr_rsi = float(df["rsi14"].iloc[-1])
    curr_atr = float(df["atr"].iloc[-1])
    curr_vol = float(df["volume"].iloc[-1])
    curr_vol_ma = float(df["vol_sma20"].iloc[-1]) if not pd.isna(df["vol_sma20"].iloc[-1]) else curr_vol
    vol_ratio = curr_vol / (curr_vol_ma + 1e-9)
    
    detected_signals = []
    
    for i in range(total_bars - scan_window, total_bars):
        bars_ago = (total_bars - 1) - i
        b_trig = bool(df["buy_trigger"].iloc[i])
        s_trig = bool(df["sell_trigger"].iloc[i])
        
        if not (b_trig or s_trig):
            continue
            
        sig_type = "BUY" if b_trig else "SELL"
        trig_bar_time = df["date"].iloc[i].strftime("%d-%b %H:%M")
        trig_close = float(df["close"].iloc[i])
        trig_vol = float(df["volume"].iloc[i])
        trig_vol_ma = float(df["vol_sma20"].iloc[i]) if not pd.isna(df["vol_sma20"].iloc[i]) else trig_vol
        trig_vol_ratio = trig_vol / (trig_vol_ma + 1e-9)
        trig_rsi = float(df["rsi14"].iloc[i])
        
        pct_from_trigger = ((curr_close - trig_close) / trig_close) * 100.0
        pct_from_ema200 = ((curr_close - curr_ema200) / curr_ema200) * 100.0
        
        # Enhanced Intraday Filters: Volume surge on breakout + RSI within 40-65
        vol_confirmed = trig_vol_ratio >= 1.2
        rsi_healthy = (42.0 <= trig_rsi <= 68.0) if sig_type == "BUY" else (trig_rsi <= 58.0)
        enhanced_score = sum([vol_confirmed, rsi_healthy])
        
        # Suitability & Intraday Risk Management
        suitability_verdict = "ACTIONABLE"
        verdict_badge = "success"
        reasons = []
        action_plan = ""
        
        # Intraday Stop Loss: Supertrend line or 200 EMA
        if sig_type == "BUY":
            stop_loss = round(min(curr_st, curr_ema200), 2)
            risk_per_share = max(curr_close - stop_loss, 0.01)
            risk_pct = (risk_per_share / curr_close) * 100.0
            target1 = round(curr_close + 1.5 * risk_per_share, 2)
            target2 = round(curr_close + 2.5 * risk_per_share, 2)
            
            if curr_close < curr_ema200 or curr_st_dir == -1:
                suitability_verdict = "NOT SUITABLE (INTRADAY BREAKDOWN)"
                verdict_badge = "danger"
                reasons.append("Breakdown: Intraday price broke below 200 EMA or Supertrend turned Red.")
                action_plan = "Do NOT Enter. The intraday bullish setup has broken down."
            elif pct_from_trigger > 2.0:
                suitability_verdict = "NOT SUITABLE (INTRADAY OVEREXTENDED)"
                verdict_badge = "warning"
                reasons.append(f"Chasing Risk: Price surged +{pct_from_trigger:.2f}% intraday from trigger bar. High risk of mean-reversion.")
                action_plan = f"Wait for intraday pullback to 200 EMA support (Rs.{curr_ema200:.2f}) before entering."
            elif risk_pct > 2.8:
                suitability_verdict = "NOT SUITABLE (INTRADAY RISK TOO WIDE)"
                verdict_badge = "warning"
                reasons.append(f"Risk Too Wide: Stop-Loss is {risk_pct:.2f}% away (>2.8% max intraday limit).")
                action_plan = f"Risk per share is too wide for intraday equity trading."
            elif bars_ago >= 18 and pct_from_trigger > 1.2:
                suitability_verdict = "NOT SUITABLE (INTRADAY STALE)"
                verdict_badge = "secondary"
                reasons.append(f"Late Session: Triggered {bars_ago} bars ({bars_ago*15} mins) ago; intraday momentum has leveled off.")
                action_plan = "Avoid late entry; wait for next trading session opening setup."
            else:
                suitability_verdict = "ACTIONABLE INTRADAY ENTRY"
                verdict_badge = "success"
                if bars_ago <= 3:
                    reasons.append(f"Fresh Intraday Trigger ({bars_ago} bars ago): High-velocity momentum!")
                else:
                    reasons.append(f"Optimal Intraday Buffer: Price holding above 200 EMA support (+{pct_from_ema200:.2f}%).")
                reasons.append(f"Intraday Risk: {risk_pct:.2f}% to Stop-Loss Rs.{stop_loss:.2f}.")
                action_plan = f"Intraday Buy: Enter at CMP Rs.{curr_close:.2f}. SL: Rs.{stop_loss:.2f}, Target 1: Rs.{target1:.2f} (1:1.5 RR), Target 2: Rs.{target2:.2f} (1:2.5 RR)."
                
        else: # SELL
            stop_loss = round(max(curr_st, curr_ema200), 2)
            risk_per_share = max(stop_loss - curr_close, 0.01)
            risk_pct = (risk_per_share / curr_close) * 100.0
            target1 = round(curr_close - 1.5 * risk_per_share, 2)
            target2 = round(curr_close - 2.5 * risk_per_share, 2)
            
            if curr_close > curr_ema200 or curr_st_dir == 1:
                suitability_verdict = "NOT SUITABLE (INTRADAY INVALIDATED)"
                verdict_badge = "danger"
                reasons.append("Breakout: Price crossed back above 200 EMA / Supertrend flipped Green.")
                action_plan = "Do NOT Short. Intraday bearish breakdown is invalidated."
            elif pct_from_trigger < -2.2:
                suitability_verdict = "NOT SUITABLE (INTRADAY OVER-DUMPED)"
                verdict_badge = "warning"
                reasons.append(f"Over-dumped: Plunged {pct_from_trigger:.2f}% intraday; high risk of short-covering spike.")
                action_plan = "Avoid aggressive intraday shorts; wait for pullback to 200 EMA."
            elif risk_pct > 2.8:
                suitability_verdict = "NOT SUITABLE (INTRADAY RISK TOO WIDE)"
                verdict_badge = "warning"
                reasons.append(f"Wide SL: Stop-Loss is {risk_pct:.2f}% above current price.")
                action_plan = "Risk exceeds intraday risk budget."
            else:
                suitability_verdict = "ACTIONABLE INTRADAY SHORT"
                verdict_badge = "danger"
                reasons.append(f"Active Breakdown: Triggered {bars_ago} bars ago; 200 EMA resistance holding.")
                reasons.append(f"Risk: {risk_pct:.2f}% to SL Rs.{stop_loss:.2f}.")
                action_plan = f"Initiate intraday short at CMP Rs.{curr_close:.2f}. SL: Rs.{stop_loss:.2f}, Target 1: Rs.{target1:.2f}."

        detected_signals.append({
            "mode": "intraday",
            "symbol": symbol,
            "name": name,
            "sector": sector,
            "timeframe": f"{interval.upper()} Intraday",
            "strategy_name": f"Intraday 200 EMA + Supertrend (10, 3)",
            "signal_type": sig_type,
            "trigger_date": trig_bar_time,
            "days_ago": round(bars_ago * 15 / 60, 1), # Hours ago
            "bars_ago": bars_ago,
            "trigger_price": round(trig_close, 2),
            "current_price": round(curr_close, 2),
            "main_ema": round(curr_ema200, 2),      # 200 EMA for Intraday
            "main_ema_name": "200 EMA",
            "supertrend": round(curr_st, 2),
            "supertrend_direction": "Bullish (Green)" if curr_st_dir == 1 else "Bearish (Red)",
            "atr": round(curr_atr, 2),
            "rsi14": round(curr_rsi, 1),
            "volume_ratio": round(vol_ratio, 2),
            "pct_from_trigger": round(pct_from_trigger, 2),
            "pct_from_ema": round(pct_from_ema200, 2),
            "stop_loss": stop_loss,
            "risk_pct": round(risk_pct, 2),
            "target1": target1,
            "target2": target2,
            "reward_risk_ratio": "1 : 1.5 / 2.5",
            "suitability": suitability_verdict,
            "verdict_badge": verdict_badge,
            "is_actionable": "ACTIONABLE" in suitability_verdict,
            "reasons": reasons,
            "action_plan": action_plan,
            "enhanced_option": {
                "trend_aligned": True,
                "vol_confirmed": bool(vol_confirmed),
                "rsi_healthy": bool(rsi_healthy),
                "pro_score": f"{enhanced_score}/2",
                "pro_status": "HIGH VOLUME INTRADAY BREAKOUT" if enhanced_score >= 2 else "STANDARD INTRADAY SETUP"
            }
        })
        
    return detected_signals

def run_full_scan(mode: str = "daily", days_lookback: int = 14, bars_lookback: int = 25, interval: str = "15m", max_workers: int = 35, buy_only: bool = True) -> dict:
    """
    Executes parallel scanning over the Dynamic Active NSE Universe.
    mode='daily': Daily 50 EMA + Supertrend (10, 3) Long Swing Focus
    mode='intraday': Intraday 15m 200 EMA + Supertrend (10, 3)
    buy_only: For spot cash swing delivery, strictly filter for BUY setups (no shorting).
    """
    t_start = time.time()
    all_signals = []
    
    # Dynamically resolve scanning universe
    active_universe = (get_active_universe() if get_active_universe else None) or LIQUID_UNIVERSE
    
    target_fn = analyze_daily_stock if mode == "daily" else (lambda item: analyze_intraday_stock(item, bars_lookback, interval))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(target_fn, item) for item in active_universe]
        for f in futures:
            try:
                res = f.result()
                if res:
                    all_signals.extend(res)
            except Exception:
                continue
                
    t_elapsed = round(time.time() - t_start, 2)
    
    # In daily swing mode, if buy_only is True, eliminate SELL signals (no shorting in equity cash)
    if mode == "daily" and buy_only:
        all_signals = [s for s in all_signals if s.get("signal_type") == "BUY"]
    
    # Sort signals: Actionable first, highest confidence score first, then freshest
    sort_key = "days_ago" if mode == "daily" else "bars_ago"
    all_signals.sort(key=lambda x: (
        not x["is_actionable"],
        -x.get("confidence_score", 0),
        x.get(sort_key, 0),
        -abs(x.get("pct_from_trigger", 0))
    ))
    
    actionable_buys = [s for s in all_signals if s["is_actionable"] and s["signal_type"] == "BUY"]
    actionable_sells = [s for s in all_signals if s["is_actionable"] and s["signal_type"] == "SELL"]
    not_suitable = [s for s in all_signals if not s["is_actionable"]]
    pro_picks = [s for s in all_signals if s["is_actionable"] and s["enhanced_option"]["vol_confirmed"]]
    elite_picks = [s for s in all_signals if s["is_actionable"] and s.get("confidence_score", 0) >= 6]
    
    return {
        "status": "success",
        "mode": mode,
        "buy_only": buy_only if mode == "daily" else False,
        "universe": f"Dynamic Live NSE Universe ({len(active_universe)} Liquid Stocks)",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scan_duration_sec": t_elapsed,
        "total_scanned_stocks": len(active_universe),
        "total_triggers_found": len(all_signals),
        "summary": {
            "actionable_buys": len(actionable_buys),
            "actionable_sells": len(actionable_sells),
            "not_suitable": len(not_suitable),
            "pro_enhanced_picks": len(pro_picks),
            "elite_confidence_picks": len(elite_picks)
        },
        "signals": all_signals
    }

def get_chart_data(symbol: str, mode: str = "daily") -> dict:
    """
    Returns OHLCV series with calculated indicators for interactive charts.
    mode='daily': Daily candles with 50 EMA, 200 EMA, Supertrend
    mode='intraday': 15m candles with 200 EMA, Supertrend
    """
    active_universe = (get_active_universe() if get_active_universe else None) or LIQUID_UNIVERSE
    item = next((x for x in active_universe if x["symbol"].upper() == symbol.upper().replace(".NS", "")), None)
    name = item["name"] if item else symbol
    
    if mode == "daily":
        df = fetch_stock_data(symbol, range_str="1y", interval="1d")
    else:
        df = fetch_stock_data(symbol, range_str="1mo", interval="15m")
        
    if df.empty:
        return {"error": f"Could not fetch chart data for {symbol}"}
        
    candles = []
    main_ema_line = []
    secondary_ema_line = []
    supertrend_line = []
    
    for _, row in df.iterrows():
        time_str = row["date"].strftime("%Y-%m-%d %H:%M") if mode == "intraday" else row["date"].strftime("%Y-%m-%d")
        candles.append({
            "time": time_str,
            "open": round(float(row["open"]), 2),
            "high": round(float(row["high"]), 2),
            "low": round(float(row["low"]), 2),
            "close": round(float(row["close"]), 2),
            "volume": int(row["volume"])
        })
        # Primary EMA
        if mode == "daily" and not pd.isna(row["ema50"]):
            main_ema_line.append({"time": time_str, "value": round(float(row["ema50"]), 2)})
        elif mode == "intraday" and not pd.isna(row["ema200"]):
            main_ema_line.append({"time": time_str, "value": round(float(row["ema200"]), 2)})
            
        # 200 EMA (for Daily)
        if mode == "daily" and not pd.isna(row["ema200"]):
            secondary_ema_line.append({"time": time_str, "value": round(float(row["ema200"]), 2)})
            
        if not pd.isna(row["supertrend"]):
            supertrend_line.append({
                "time": time_str, 
                "value": round(float(row["supertrend"]), 2),
                "color": "#10b981" if row["st_dir"] == 1 else "#ef4444"
            })
            
    stock_item = {"symbol": symbol, "name": name, "sector": item["sector"] if item else "General"}
    signals = analyze_daily_stock(stock_item) if mode == "daily" else analyze_intraday_stock(stock_item)
    
    return {
        "symbol": symbol.upper().replace(".NS", ""),
        "name": name,
        "mode": mode,
        "candles": candles,
        "main_ema": main_ema_line,
        "main_ema_name": "50 EMA" if mode == "daily" else "200 EMA (Intraday)",
        "secondary_ema": secondary_ema_line,
        "supertrend": supertrend_line,
        "recent_signals": signals
    }

if __name__ == "__main__":
    print(f"[*] Testing Daily Scanner across Nifty 500 companies...")
    d_res = run_full_scan(mode="daily", days_lookback=7)
    print(f"[✓] Daily scan completed in {d_res['scan_duration_sec']}s. Found: {d_res['total_triggers_found']} triggers.")
    
    print(f"\n[*] Testing Intraday Scanner (15m 200 EMA + Supertrend)...")
    i_res = run_full_scan(mode="intraday", bars_lookback=25)
    print(f"[✓] Intraday scan completed in {i_res['scan_duration_sec']}s. Found: {i_res['total_triggers_found']} triggers.")
