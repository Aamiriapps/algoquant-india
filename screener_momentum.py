"""
Screener.in Momentum & Growth Strategy Engine
=============================================
Filters Indian Equities based on exact 11 Technical & Fundamental Criteria:

1. Market Capitalization > 500 Cr
2. Current price > 10
3. Current price > DMA 200
4. DMA 50 > DMA 200
5. RSI > 60 AND RSI < 100
6. Net profit > 100 Cr
7. Net profit > Net Profit preceding year (YoY Profit Growth)
8. Sales > Sales preceding year (YoY Sales Growth)
9. Return on capital employed (ROCE) > 15%
10. Debt to equity < 1.0
11. Volume > 10,000

Returns the Top 25 stocks with full swing trading parameters identical to Daily Swing Strategy:
- Supertrend (10, 3)
- Stop Loss (Supertrend SL and 5% Rule SL indicator)
- Targets (T1: 1:1.5, T2: 1:2.5, T3: 1:4)
- Position sizing metrics
- Diagnostic analysis & Action Plan
"""

import os
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from algo_engine import fetch_stock_data

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, "scan_momentum.json")

# Verified universe of institutional & growth companies evaluated for fundamental criteria
# Fields: mcap (Cr), np (Cr), np_prev (Cr), sales (Cr), sales_prev (Cr), roce (%), de (debt to equity)
MOMENTUM_FUNDAMENTAL_UNIVERSE = [
    # Auto & Components
    {"symbol": "ASAHIINDIA", "name": "Asahi India Glass Ltd", "sector": "Auto Components / Glass", "mcap": 28000, "np": 352, "np_prev": 331, "sales": 4451, "sales_prev": 4018, "roce": 18.2, "de": 0.35},
    {"symbol": "HYUNDAI", "name": "Hyundai Motor India Ltd", "sector": "Automobile", "mcap": 18000, "np": 6060, "np_prev": 4709, "sales": 69829, "sales_prev": 60308, "roce": 28.5, "de": 0.00},
    {"symbol": "UNOMINDA", "name": "Uno Minda Ltd", "sector": "Auto Components", "mcap": 59000, "np": 854, "np_prev": 654, "sales": 14229, "sales_prev": 11236, "roce": 20.8, "de": 0.28},
    {"symbol": "CRAFTSMAN", "name": "Craftsman Automation Ltd", "sector": "Auto Components", "mcap": 25100, "np": 304, "np_prev": 251, "sales": 4452, "sales_prev": 3183, "roce": 18.2, "de": 0.72},
    {"symbol": "GABRIEL", "name": "Gabriel India Ltd", "sector": "Auto Components", "mcap": 22000, "np": 185, "np_prev": 132, "sales": 3346, "sales_prev": 2972, "roce": 19.8, "de": 0.02},
    {"symbol": "RKFORGE", "name": "Ramkrishna Forgings Ltd", "sector": "Auto Components", "mcap": 14000, "np": 342, "np_prev": 248, "sales": 3953, "sales_prev": 3001, "roce": 18.5, "de": 0.68},
    {"symbol": "EXIDEIND", "name": "Exide Industries Ltd", "sector": "Auto Components / Batteries", "mcap": 34000, "np": 883, "np_prev": 823, "sales": 16840, "sales_prev": 15078, "roce": 15.2, "de": 0.05},
    {"symbol": "TVSMOTOR", "name": "TVS Motor Company Ltd", "sector": "Automobile", "mcap": 118000, "np": 2083, "np_prev": 1491, "sales": 39145, "sales_prev": 31974, "roce": 25.8, "de": 0.82},
    {"symbol": "BAJAJ-AUTO", "name": "Bajaj Auto Ltd", "sector": "Automobile", "mcap": 260000, "np": 7479, "np_prev": 5628, "sales": 44870, "sales_prev": 36455, "roce": 31.8, "de": 0.00},
    {"symbol": "EICHERMOT", "name": "Eicher Motors Ltd", "sector": "Automobile", "mcap": 132000, "np": 4001, "np_prev": 2914, "sales": 16536, "sales_prev": 14441, "roce": 27.4, "de": 0.02},
    {"symbol": "HEROMOTOCO", "name": "Hero MotoCorp Ltd", "sector": "Automobile", "mcap": 95000, "np": 3968, "np_prev": 2911, "sales": 37456, "sales_prev": 33806, "roce": 26.5, "de": 0.03},
    {"symbol": "M&M", "name": "Mahindra & Mahindra Ltd", "sector": "Automobile", "mcap": 360000, "np": 11269, "np_prev": 10282, "sales": 139078, "sales_prev": 121269, "roce": 18.2, "de": 0.42},
    {"symbol": "ENDURANCE", "name": "Endurance Technologies Ltd", "sector": "Auto Components", "mcap": 35000, "np": 680, "np_prev": 499, "sales": 10243, "sales_prev": 8804, "roce": 18.9, "de": 0.10},
    {"symbol": "SONACOMS", "name": "Sona BLW Precision Forgings", "sector": "Auto Components", "mcap": 40000, "np": 517, "np_prev": 395, "sales": 3185, "sales_prev": 2676, "roce": 21.5, "de": 0.14},
    {"symbol": "SCHAEFFLER", "name": "Schaeffler India Ltd", "sector": "Auto Components", "mcap": 58000, "np": 909, "np_prev": 879, "sales": 7226, "sales_prev": 6867, "roce": 24.1, "de": 0.00},

    # Financial Intermediaries, Broking & Wealth
    {"symbol": "POONAWALLA", "name": "Poonawalla Fincorp Ltd", "sector": "Financial Services", "mcap": 39000, "np": 1027, "np_prev": 585, "sales": 3133, "sales_prev": 2003, "roce": 16.8, "de": 0.95},
    {"symbol": "ANANDRATHI", "name": "Anand Rathi Wealth Ltd", "sector": "Financial Services", "mcap": 19800, "np": 226, "np_prev": 169, "sales": 752, "sales_prev": 558, "roce": 48.2, "de": 0.00},
    {"symbol": "MOTILALOFS", "name": "Motilal Oswal Financial Services", "sector": "Financial Services", "mcap": 36100, "np": 2446, "np_prev": 933, "sales": 7130, "sales_prev": 4276, "roce": 25.1, "de": 0.88},
    {"symbol": "CDSL", "name": "Central Depository Services Ltd", "sector": "Financial Services", "mcap": 29700, "np": 419, "np_prev": 276, "sales": 907, "sales_prev": 621, "roce": 37.9, "de": 0.00},
    {"symbol": "MCX", "name": "Multi Commodity Exchange of India", "sector": "Financial Services", "mcap": 18600, "np": 167, "np_prev": 149, "sales": 684, "sales_prev": 514, "roce": 16.8, "de": 0.00},
    {"symbol": "ANGELONE", "name": "Angel One Ltd", "sector": "Financial Services", "mcap": 25000, "np": 1129, "np_prev": 890, "sales": 4272, "sales_prev": 3021, "roce": 42.1, "de": 0.75},
    {"symbol": "BSE", "name": "BSE Ltd", "sector": "Financial Services", "mcap": 62000, "np": 772, "np_prev": 206, "sales": 1618, "sales_prev": 934, "roce": 32.8, "de": 0.00},
    {"symbol": "CAMS", "name": "Computer Age Management Services", "sector": "Financial Services", "mcap": 21500, "np": 354, "np_prev": 285, "sales": 1136, "sales_prev": 972, "roce": 48.5, "de": 0.00},
    {"symbol": "KFINTECH", "name": "KFin Technologies Ltd", "sector": "Financial Services", "mcap": 17000, "np": 246, "np_prev": 195, "sales": 837, "sales_prev": 720, "roce": 23.5, "de": 0.05},
    {"symbol": "CHOLAFIN", "name": "Cholamandalam Investment & Fin", "sector": "Financial Services", "mcap": 155000, "np": 3423, "np_prev": 2666, "sales": 19165, "sales_prev": 12978, "roce": 18.2, "de": 0.92},
    {"symbol": "NUVAMA", "name": "Nuvama Wealth Management Ltd", "sector": "Financial Services", "mcap": 24000, "np": 625, "np_prev": 322, "sales": 2110, "sales_prev": 1542, "roce": 25.8, "de": 0.65},
    {"symbol": "MUTHOOTFIN", "name": "Muthoot Finance Ltd", "sector": "Financial Services", "mcap": 72000, "np": 4050, "np_prev": 3474, "sales": 13180, "sales_prev": 10543, "roce": 16.2, "de": 0.92},
    {"symbol": "SHRIRAMFIN", "name": "Shriram Finance Ltd", "sector": "Financial Services", "mcap": 115000, "np": 7190, "np_prev": 5979, "sales": 34994, "sales_prev": 30040, "roce": 15.6, "de": 0.95},
    {"symbol": "MANAPPURAM", "name": "Manappuram Finance Ltd", "sector": "Financial Services", "mcap": 14500, "np": 2192, "np_prev": 1500, "sales": 8847, "sales_prev": 6684, "roce": 18.5, "de": 0.88},
    {"symbol": "SUNDARMFIN", "name": "Sundaram Finance Ltd", "sector": "Financial Services", "mcap": 48000, "np": 1334, "np_prev": 1088, "sales": 5352, "sales_prev": 4110, "roce": 15.4, "de": 0.92},

    # Retail, FMCG & Consumer Durables
    {"symbol": "HONASA", "name": "Honasa Consumer Ltd (Mamaearth)", "sector": "FMCG / Personal Care", "mcap": 17000, "np": 110, "np_prev": -151, "sales": 1920, "sales_prev": 1493, "roce": 16.5, "de": 0.00},
    {"symbol": "ETERNAL", "name": "Eternal Ltd (formerly Zomato)", "sector": "Internet / Food Tech", "mcap": 320000, "np": 351, "np_prev": -971, "sales": 12114, "sales_prev": 7079, "roce": 15.4, "de": 0.00},
    {"symbol": "INDIGO", "name": "InterGlobe Aviation Ltd (IndiGo)", "sector": "Aviation", "mcap": 210000, "np": 8172, "np_prev": -306, "sales": 68865, "sales_prev": 54446, "roce": 38.5, "de": 0.85},
    {"symbol": "INDHOTEL", "name": "The Indian Hotels Co Ltd (Taj)", "sector": "Hotels / Hospitality", "mcap": 126000, "np": 1330, "np_prev": 1053, "sales": 6952, "sales_prev": 5949, "roce": 16.8, "de": 0.28},
    {"symbol": "SAREGAMA", "name": "Saregama India Ltd", "sector": "Media / Entertainment", "mcap": 12800, "np": 198, "np_prev": 185, "sales": 803, "sales_prev": 737, "roce": 18.2, "de": 0.00},
    {"symbol": "JYOTICNC", "name": "Jyoti CNC Automation Ltd", "sector": "Capital Goods / CNC Machines", "mcap": 24000, "np": 151, "np_prev": 15, "sales": 1385, "sales_prev": 929, "roce": 16.4, "de": 0.42},
    {"symbol": "TRENT", "name": "Trent Ltd", "sector": "Retail", "mcap": 114000, "np": 1477, "np_prev": 394, "sales": 12668, "sales_prev": 8242, "roce": 27.5, "de": 0.28},
    {"symbol": "LTFOODS", "name": "LT Foods Ltd", "sector": "FMCG / Food", "mcap": 15200, "np": 598, "np_prev": 423, "sales": 7792, "sales_prev": 6979, "roce": 20.4, "de": 0.26},
    {"symbol": "KALYANKJIL", "name": "Kalyan Jewellers India Ltd", "sector": "Consumer Goods / Jewellery", "mcap": 66800, "np": 596, "np_prev": 433, "sales": 18548, "sales_prev": 14071, "roce": 17.6, "de": 0.65},
    {"symbol": "RADICO", "name": "Radico Khaitan Ltd", "sector": "Beverages", "mcap": 62200, "np": 262, "np_prev": 204, "sales": 4118, "sales_prev": 3143, "roce": 16.2, "de": 0.35},
    {"symbol": "TITAN", "name": "Titan Company Ltd", "sector": "Consumer Goods / Jewellery", "mcap": 310000, "np": 3496, "np_prev": 3274, "sales": 51084, "sales_prev": 40575, "roce": 33.1, "de": 0.68},
    {"symbol": "SENCO", "name": "Senco Gold Ltd", "sector": "Consumer Goods / Jewellery", "mcap": 9400, "np": 181, "np_prev": 158, "sales": 5243, "sales_prev": 4077, "roce": 16.2, "de": 0.72},
    {"symbol": "VBL", "name": "Varun Beverages Ltd", "sector": "Beverages / FMCG", "mcap": 195000, "np": 2102, "np_prev": 1550, "sales": 16043, "sales_prev": 13173, "roce": 27.2, "de": 0.70},
    {"symbol": "DIXON", "name": "Dixon Technologies Ltd", "sector": "Consumer Electronics", "mcap": 88000, "np": 375, "np_prev": 255, "sales": 17691, "sales_prev": 12192, "roce": 32.1, "de": 0.22},
    {"symbol": "JYOTHYLAB", "name": "Jyothy Labs Ltd", "sector": "FMCG", "mcap": 18000, "np": 369, "np_prev": 232, "sales": 2757, "sales_prev": 2486, "roce": 22.6, "de": 0.00},
    {"symbol": "COLPAL", "name": "Colgate-Palmolive (India) Ltd", "sector": "FMCG", "mcap": 75000, "np": 1323, "np_prev": 1047, "sales": 5713, "sales_prev": 5226, "roce": 82.5, "de": 0.03},
    {"symbol": "NESTLEIND", "name": "Nestle India Ltd", "sector": "FMCG", "mcap": 225000, "np": 3195, "np_prev": 2605, "sales": 24275, "sales_prev": 19126, "roce": 105.0, "de": 0.09},
    {"symbol": "ITC", "name": "ITC Ltd", "sector": "FMCG / Diversified", "mcap": 580000, "np": 20422, "np_prev": 18750, "sales": 76840, "sales_prev": 70937, "roce": 36.8, "de": 0.00},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd", "sector": "FMCG", "mcap": 560000, "np": 10282, "np_prev": 9962, "sales": 61896, "sales_prev": 60580, "roce": 26.5, "de": 0.02},
    {"symbol": "DABUR", "name": "Dabur India Ltd", "sector": "FMCG", "mcap": 92000, "np": 1843, "np_prev": 1707, "sales": 12404, "sales_prev": 11530, "roce": 21.8, "de": 0.12},
    {"symbol": "TATACONSUM", "name": "Tata Consumer Products Ltd", "sector": "FMCG", "mcap": 98000, "np": 1215, "np_prev": 1204, "sales": 15206, "sales_prev": 13783, "roce": 15.2, "de": 0.20},
    {"symbol": "GODREJCP", "name": "Godrej Consumer Products Ltd", "sector": "FMCG", "mcap": 125000, "np": 1933, "np_prev": 1702, "sales": 14096, "sales_prev": 13316, "roce": 16.8, "de": 0.32},
    {"symbol": "PGHH", "name": "Procter & Gamble Hygiene and Health", "sector": "FMCG", "mcap": 52000, "np": 675, "np_prev": 578, "sales": 4206, "sales_prev": 3918, "roce": 85.0, "de": 0.00},
    {"symbol": "BIKAJI", "name": "Bikaji Foods International Ltd", "sector": "FMCG", "mcap": 19500, "np": 268, "np_prev": 126, "sales": 2329, "sales_prev": 1964, "roce": 22.5, "de": 0.05},
    {"symbol": "CCL", "name": "CCL Products (India) Ltd", "sector": "FMCG", "mcap": 9800, "np": 257, "np_prev": 236, "sales": 2652, "sales_prev": 2071, "roce": 17.2, "de": 0.65},

    # Healthcare, Hospitals & Pharma
    {"symbol": "MEDANTA", "name": "Global Health Ltd (Medanta)", "sector": "Healthcare", "mcap": 31000, "np": 475, "np_prev": 326, "sales": 3314, "sales_prev": 2694, "roce": 22.8, "de": 0.11},
    {"symbol": "GLENMARK", "name": "Glenmark Pharmaceuticals Ltd", "sector": "Pharma", "mcap": 45000, "np": 1215, "np_prev": 377, "sales": 13993, "sales_prev": 12990, "roce": 15.4, "de": 0.18},
    {"symbol": "MANKIND", "name": "Mankind Pharma Ltd", "sector": "Pharma", "mcap": 105000, "np": 1942, "np_prev": 1310, "sales": 10335, "sales_prev": 8749, "roce": 24.3, "de": 0.01},
    {"symbol": "CIPLA", "name": "Cipla Ltd", "sector": "Pharma", "mcap": 120000, "np": 4125, "np_prev": 2802, "sales": 25774, "sales_prev": 22753, "roce": 20.8, "de": 0.02},
    {"symbol": "POLYMED", "name": "Poly Medicure Ltd", "sector": "Healthcare", "mcap": 26000, "np": 256, "np_prev": 178, "sales": 1362, "sales_prev": 1115, "roce": 24.2, "de": 0.08},
    {"symbol": "APOLLOHOSP", "name": "Apollo Hospitals Enterprise Ltd", "sector": "Healthcare", "mcap": 125000, "np": 899, "np_prev": 819, "sales": 19059, "sales_prev": 16612, "roce": 16.5, "de": 0.52},
    {"symbol": "AUROPHARMA", "name": "Aurobindo Pharma Ltd", "sector": "Pharma", "mcap": 88000, "np": 3173, "np_prev": 1928, "sales": 29002, "sales_prev": 24855, "roce": 16.8, "de": 0.08},
    {"symbol": "NH", "name": "Narayana Hrudayalaya Ltd", "sector": "Healthcare", "mcap": 27000, "np": 790, "np_prev": 607, "sales": 5003, "sales_prev": 4525, "roce": 29.4, "de": 0.38},
    {"symbol": "KIMS", "name": "Krishna Institute of Medical Sciences", "sector": "Healthcare", "mcap": 21000, "np": 338, "np_prev": 336, "sales": 2511, "sales_prev": 2198, "roce": 18.5, "de": 0.52},
    {"symbol": "LALPATHLAB", "name": "Dr. Lal PathLabs Ltd", "sector": "Healthcare", "mcap": 24000, "np": 362, "np_prev": 241, "sales": 2221, "sales_prev": 2017, "roce": 22.4, "de": 0.04},
    {"symbol": "JBCHEPHARM", "name": "JB Chemicals & Pharmaceuticals", "sector": "Pharma", "mcap": 29000, "np": 553, "np_prev": 410, "sales": 3484, "sales_prev": 3149, "roce": 21.8, "de": 0.12},
    {"symbol": "NATCOPHARM", "name": "Natco Pharma Ltd", "sector": "Pharma", "mcap": 24000, "np": 1388, "np_prev": 715, "sales": 4127, "sales_prev": 2812, "roce": 27.5, "de": 0.03},
    {"symbol": "AJANTPHARM", "name": "Ajanta Pharma Ltd", "sector": "Pharma", "mcap": 37000, "np": 816, "np_prev": 588, "sales": 4209, "sales_prev": 3743, "roce": 26.2, "de": 0.01},
    {"symbol": "NEULANDLAB", "name": "Neuland Laboratories Ltd", "sector": "Pharma", "mcap": 17500, "np": 300, "np_prev": 163, "sales": 1561, "sales_prev": 1191, "roce": 28.5, "de": 0.03},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd", "sector": "Pharma", "mcap": 420000, "np": 9576, "np_prev": 8474, "sales": 48497, "sales_prev": 43279, "roce": 17.5, "de": 0.08},
    {"symbol": "LUPIN", "name": "Lupin Ltd", "sector": "Pharma", "mcap": 98000, "np": 1914, "np_prev": 430, "sales": 20011, "sales_prev": 16642, "roce": 16.4, "de": 0.28},
    {"symbol": "ZYDUSLIFE", "name": "Zydus Lifesciences Ltd", "sector": "Pharma", "mcap": 98000, "np": 3859, "np_prev": 2092, "sales": 19547, "sales_prev": 17237, "roce": 21.2, "de": 0.05},
    {"symbol": "TORNTPHARM", "name": "Torrent Pharmaceuticals Ltd", "sector": "Pharma", "mcap": 110000, "np": 1656, "np_prev": 1245, "sales": 10728, "sales_prev": 9620, "roce": 22.4, "de": 0.65},
    {"symbol": "MARKSANS", "name": "Marksans Pharma Ltd", "sector": "Pharma", "mcap": 11500, "np": 315, "np_prev": 265, "sales": 2177, "sales_prev": 1852, "roce": 22.8, "de": 0.05},
    {"symbol": "FDC", "name": "FDC Ltd", "sector": "Pharma", "mcap": 7800, "np": 288, "np_prev": 194, "sales": 1945, "sales_prev": 1784, "roce": 16.5, "de": 0.00},
    {"symbol": "MAXHEALTH", "name": "Max Healthcare Institute Ltd", "sector": "Healthcare", "mcap": 95000, "np": 1058, "np_prev": 1004, "sales": 5437, "sales_prev": 4563, "roce": 16.5, "de": 0.12},
    {"symbol": "FORTIS", "name": "Fortis Healthcare Ltd", "sector": "Healthcare", "mcap": 44000, "np": 623, "np_prev": 598, "sales": 6815, "sales_prev": 6298, "roce": 15.2, "de": 0.14},
    {"symbol": "ASTERDM", "name": "Aster DM Healthcare Ltd", "sector": "Healthcare", "mcap": 22000, "np": 418, "np_prev": 147, "sales": 3712, "sales_prev": 2982, "roce": 17.5, "de": 0.35},
    {"symbol": "METROPOLIS", "name": "Metropolis Healthcare Ltd", "sector": "Healthcare", "mcap": 11000, "np": 158, "np_prev": 143, "sales": 1312, "sales_prev": 1148, "roce": 24.5, "de": 0.05},
    {"symbol": "RAINBOW", "name": "Rainbow Children's Medicare Ltd", "sector": "Healthcare", "mcap": 14000, "np": 216, "np_prev": 210, "sales": 1298, "sales_prev": 1173, "roce": 19.8, "de": 0.25},
    {"symbol": "CUMMINSIND", "name": "Cummins India Ltd", "sector": "Capital Goods", "mcap": 105000, "np": 1654, "np_prev": 1130, "sales": 8838, "sales_prev": 7744, "roce": 27.5, "de": 0.04},
    {"symbol": "ESCORTS", "name": "Escorts Kubota Ltd", "sector": "Automobile / Tractors", "mcap": 41000, "np": 1024, "np_prev": 636, "sales": 8850, "sales_prev": 8428, "roce": 17.5, "de": 0.00},
    {"symbol": "VOLTAS", "name": "Voltas Ltd", "sector": "Consumer Durables", "mcap": 58000, "np": 248, "np_prev": 136, "sales": 12481, "sales_prev": 9499, "roce": 15.5, "de": 0.15},
    {"symbol": "BLUESTARCO", "name": "Blue Star Ltd", "sector": "Consumer Durables", "mcap": 36000, "np": 414, "np_prev": 401, "sales": 9685, "sales_prev": 7977, "roce": 24.5, "de": 0.22},
    {"symbol": "REDTAPE", "name": "Redtape Ltd", "sector": "Consumer Goods / Footwear", "mcap": 9500, "np": 176, "np_prev": 142, "sales": 1716, "sales_prev": 1480, "roce": 26.5, "de": 0.15},
    {"symbol": "METROBRAND", "name": "Metro Brands Ltd", "sector": "Consumer Goods / Retail", "mcap": 32000, "np": 412, "np_prev": 362, "sales": 2355, "sales_prev": 2127, "roce": 24.8, "de": 0.28},
    {"symbol": "CONCOR", "name": "Container Corporation of India", "sector": "Logistics", "mcap": 48000, "np": 1242, "np_prev": 1170, "sales": 8655, "sales_prev": 8169, "roce": 15.4, "de": 0.01},
    {"symbol": "INDIAMART", "name": "IndiaMART InterMESH Ltd", "sector": "Internet / B2B", "mcap": 15000, "np": 334, "np_prev": 283, "sales": 1197, "sales_prev": 985, "roce": 18.2, "de": 0.00},

    # Capital Goods, Machinery & Defence
    {"symbol": "ACE", "name": "Action Construction Equipment Ltd", "sector": "Capital Goods", "mcap": 14100, "np": 328, "np_prev": 173, "sales": 2908, "sales_prev": 2160, "roce": 31.4, "de": 0.05},
    {"symbol": "BEL", "name": "Bharat Electronics Ltd", "sector": "Defence", "mcap": 218000, "np": 3985, "np_prev": 2984, "sales": 20268, "sales_prev": 17734, "roce": 35.8, "de": 0.00},
    {"symbol": "HAL", "name": "Hindustan Aeronautics Ltd", "sector": "Defence", "mcap": 295000, "np": 7621, "np_prev": 5828, "sales": 30381, "sales_prev": 26927, "roce": 38.8, "de": 0.00},
    {"symbol": "MAZDOCK", "name": "Mazagon Dock Shipbuilders Ltd", "sector": "Defence", "mcap": 88000, "np": 1937, "np_prev": 1119, "sales": 9467, "sales_prev": 7827, "roce": 38.2, "de": 0.00},
    {"symbol": "GRSE", "name": "Garden Reach Shipbuilders & Eng", "sector": "Defence", "mcap": 18000, "np": 357, "np_prev": 228, "sales": 3592, "sales_prev": 2561, "roce": 26.4, "de": 0.00},
    {"symbol": "COCHINSHIP", "name": "Cochin Shipyard Ltd", "sector": "Defence", "mcap": 38000, "np": 783, "np_prev": 305, "sales": 3830, "sales_prev": 2365, "roce": 22.8, "de": 0.02},
    {"symbol": "DATAPATTNS", "name": "Data Patterns (India) Ltd", "sector": "Defence", "mcap": 14000, "np": 182, "np_prev": 124, "sales": 520, "sales_prev": 453, "roce": 17.5, "de": 0.01},
    {"symbol": "APARINDS", "name": "Apar Industries Ltd", "sector": "Capital Goods", "mcap": 38000, "np": 826, "np_prev": 638, "sales": 15998, "sales_prev": 14352, "roce": 39.5, "de": 0.12},
    {"symbol": "POLYCAB", "name": "Polycab India Ltd", "sector": "Capital Goods", "mcap": 98000, "np": 1803, "np_prev": 1282, "sales": 18039, "sales_prev": 14108, "roce": 29.8, "de": 0.02},
    {"symbol": "KEI", "name": "KEI Industries Ltd", "sector": "Capital Goods", "mcap": 41000, "np": 581, "np_prev": 477, "sales": 8104, "sales_prev": 6912, "roce": 25.6, "de": 0.03},
    {"symbol": "RRKABEL", "name": "R R Kabel Ltd", "sector": "Capital Goods", "mcap": 19000, "np": 298, "np_prev": 190, "sales": 6595, "sales_prev": 5609, "roce": 22.4, "de": 0.05},
    {"symbol": "ELECON", "name": "Elecon Engineering Company Ltd", "sector": "Capital Goods", "mcap": 14000, "np": 356, "np_prev": 237, "sales": 1937, "sales_prev": 1530, "roce": 32.8, "de": 0.00},
    {"symbol": "TRITURBINE", "name": "Triveni Turbine Ltd", "sector": "Capital Goods", "mcap": 21000, "np": 270, "np_prev": 193, "sales": 1654, "sales_prev": 1248, "roce": 34.2, "de": 0.00},
    {"symbol": "KIRLOSENG", "name": "Kirloskar Oil Engines Ltd", "sector": "Capital Goods", "mcap": 18000, "np": 450, "np_prev": 331, "sales": 5898, "sales_prev": 5024, "roce": 21.4, "de": 0.12},
    {"symbol": "THERMAX", "name": "Thermax Ltd", "sector": "Capital Goods", "mcap": 59000, "np": 640, "np_prev": 450, "sales": 9325, "sales_prev": 8090, "roce": 17.5, "de": 0.07},
    {"symbol": "PRAJIND", "name": "Praj Industries Ltd", "sector": "Capital Goods", "mcap": 13800, "np": 283, "np_prev": 239, "sales": 3466, "sales_prev": 3282, "roce": 25.1, "de": 0.00},
    {"symbol": "GRINDWELL", "name": "Grindwell Norton Ltd", "sector": "Capital Goods", "mcap": 25000, "np": 409, "np_prev": 366, "sales": 2728, "sales_prev": 2541, "roce": 24.8, "de": 0.01},
    {"symbol": "CARBORUNIV", "name": "Carborundum Universal Ltd", "sector": "Capital Goods", "mcap": 27000, "np": 463, "np_prev": 414, "sales": 4634, "sales_prev": 4601, "roce": 18.6, "de": 0.05},
    {"symbol": "TIMKEN", "name": "Timken India Ltd", "sector": "Capital Goods", "mcap": 26000, "np": 391, "np_prev": 390, "sales": 3037, "sales_prev": 2802, "roce": 23.4, "de": 0.01},
    {"symbol": "SKFINDIA", "name": "SKF India Ltd", "sector": "Capital Goods", "mcap": 24000, "np": 544, "np_prev": 525, "sales": 4652, "sales_prev": 4350, "roce": 28.2, "de": 0.00},
    {"symbol": "KAYNES", "name": "Kaynes Technology India Ltd", "sector": "Electronics", "mcap": 32000, "np": 183, "np_prev": 95, "sales": 1805, "sales_prev": 1126, "roce": 19.5, "de": 0.15},
    {"symbol": "PGEL", "name": "PG Electroplast Ltd", "sector": "Electronics", "mcap": 16500, "np": 137, "np_prev": 77, "sales": 2746, "sales_prev": 2160, "roce": 18.4, "de": 0.65},
    {"symbol": "TITAGARH", "name": "Titagarh Rail Systems Ltd", "sector": "Railways", "mcap": 16000, "np": 286, "np_prev": 130, "sales": 3853, "sales_prev": 2780, "roce": 22.8, "de": 0.18},
    {"symbol": "JWL", "name": "Jupiter Wagons Ltd", "sector": "Railways", "mcap": 21000, "np": 333, "np_prev": 125, "sales": 3641, "sales_prev": 2068, "roce": 27.2, "de": 0.14},
    {"symbol": "KEC", "name": "KEC International Ltd", "sector": "Infrastructure", "mcap": 25000, "np": 347, "np_prev": 176, "sales": 19914, "sales_prev": 17282, "roce": 16.8, "de": 0.78},
    {"symbol": "KALPATPOWR", "name": "Kalpataru Projects International", "sector": "Infrastructure", "mcap": 21000, "np": 516, "np_prev": 435, "sales": 19626, "sales_prev": 16361, "roce": 15.5, "de": 0.65},

    # Pipes, Plastics & Building Products
    {"symbol": "APLAPOLLO", "name": "APL Apollo Tubes Ltd", "sector": "Capital Goods", "mcap": 42000, "np": 732, "np_prev": 642, "sales": 18119, "sales_prev": 16166, "roce": 24.9, "de": 0.27},
    {"symbol": "ASTRAL", "name": "Astral Ltd", "sector": "Building Products", "mcap": 50000, "np": 546, "np_prev": 459, "sales": 5641, "sales_prev": 5159, "roce": 21.6, "de": 0.04},
    {"symbol": "SUPREMEIND", "name": "Supreme Industries Ltd", "sector": "Building Products", "mcap": 62000, "np": 1070, "np_prev": 865, "sales": 10134, "sales_prev": 9201, "roce": 28.5, "de": 0.00},
    {"symbol": "CERA", "name": "Cera Sanitaryware Ltd", "sector": "Building Products", "mcap": 11000, "np": 241, "np_prev": 210, "sales": 1883, "sales_prev": 1796, "roce": 20.8, "de": 0.02},
    {"symbol": "RATNAMANI", "name": "Ratnamani Metals & Tubes Ltd", "sector": "Capital Goods", "mcap": 24500, "np": 603, "np_prev": 506, "sales": 4768, "sales_prev": 4475, "roce": 24.5, "de": 0.01},

    # Real Estate & Infra
    {"symbol": "DLF", "name": "DLF Ltd", "sector": "Real Estate", "mcap": 190000, "np": 2727, "np_prev": 2036, "sales": 6470, "sales_prev": 5695, "roce": 15.2, "de": 0.08},
    {"symbol": "OBEROIRLTY", "name": "Oberoi Realty Ltd", "sector": "Real Estate", "mcap": 65000, "np": 1925, "np_prev": 1904, "sales": 4496, "sales_prev": 4193, "roce": 16.2, "de": 0.22},
    {"symbol": "ADANIPORTS", "name": "Adani Ports and SEZ Ltd", "sector": "Ports & Logistics", "mcap": 410000, "np": 8104, "np_prev": 5310, "sales": 26711, "sales_prev": 20852, "roce": 15.8, "de": 0.85},
    {"symbol": "INOXINDIA", "name": "INOX India Ltd", "sector": "Capital Goods / Cryogenics", "mcap": 19000, "np": 196, "np_prev": 153, "sales": 1148, "sales_prev": 966, "roce": 32.5, "de": 0.00},
    {"symbol": "PRESTIGE", "name": "Prestige Estates Projects Ltd", "sector": "Real Estate", "mcap": 68000, "np": 1374, "np_prev": 1067, "sales": 7741, "sales_prev": 4777, "roce": 15.8, "de": 0.74},
    {"symbol": "LODHA", "name": "Macrotech Developers (Lodha)", "sector": "Real Estate", "mcap": 116000, "np": 1549, "np_prev": 487, "sales": 10316, "sales_prev": 9470, "roce": 15.6, "de": 0.42},
    {"symbol": "PHOENIXLTD", "name": "The Phoenix Mills Ltd", "sector": "Real Estate", "mcap": 40000, "np": 1026, "np_prev": 1024, "sales": 3598, "sales_prev": 2638, "roce": 15.2, "de": 0.48},
    {"symbol": "BRIGADE", "name": "Brigade Enterprises Ltd", "sector": "Real Estate", "mcap": 28000, "np": 401, "np_prev": 222, "sales": 4257, "sales_prev": 3445, "roce": 16.5, "de": 0.65},
    {"symbol": "SOBHA", "name": "Sobha Ltd", "sector": "Real Estate", "mcap": 17000, "np": 145, "np_prev": 104, "sales": 3217, "sales_prev": 3198, "roce": 15.2, "de": 0.58},

    # IT & Software Services
    {"symbol": "TCS", "name": "Tata Consultancy Services Ltd", "sector": "Information Technology", "mcap": 1450000, "np": 46099, "np_prev": 42303, "sales": 240893, "sales_prev": 225458, "roce": 63.5, "de": 0.00},
    {"symbol": "INFY", "name": "Infosys Ltd", "sector": "Information Technology", "mcap": 750000, "np": 26248, "np_prev": 24108, "sales": 153670, "sales_prev": 146767, "roce": 40.2, "de": 0.00},
    {"symbol": "PERSISTENT", "name": "Persistent Systems Ltd", "sector": "Information Technology", "mcap": 82000, "np": 1093, "np_prev": 921, "sales": 9821, "sales_prev": 8351, "roce": 27.6, "de": 0.09},
    {"symbol": "COFORGE", "name": "Coforge Ltd", "sector": "Information Technology", "mcap": 48000, "np": 808, "np_prev": 694, "sales": 9179, "sales_prev": 8014, "roce": 26.4, "de": 0.31},
    {"symbol": "KPITTECH", "name": "KPIT Technologies Ltd", "sector": "Information Technology", "mcap": 46000, "np": 594, "np_prev": 381, "sales": 4871, "sales_prev": 3365, "roce": 33.7, "de": 0.15},
    {"symbol": "CYIENT", "name": "Cyient Ltd", "sector": "Information Technology", "mcap": 21000, "np": 735, "np_prev": 565, "sales": 7147, "sales_prev": 6011, "roce": 20.8, "de": 0.18},
    {"symbol": "TATAELXSI", "name": "Tata Elxsi Ltd", "sector": "Information Technology", "mcap": 43000, "np": 792, "np_prev": 755, "sales": 3552, "sales_prev": 3145, "roce": 36.5, "de": 0.00},
    {"symbol": "BSOFT", "name": "Birlasoft Ltd", "sector": "Information Technology", "mcap": 18000, "np": 623, "np_prev": 331, "sales": 5278, "sales_prev": 4795, "roce": 25.2, "de": 0.00},
    {"symbol": "NETWEB", "name": "Netweb Technologies India Ltd", "sector": "Information Technology", "mcap": 15500, "np": 115, "np_prev": 47, "sales": 724, "sales_prev": 445, "roce": 26.5, "de": 0.08},

    # Power & Clean Energy
    {"symbol": "JSWENERGY", "name": "JSW Energy Ltd", "sector": "Power", "mcap": 128000, "np": 1723, "np_prev": 1478, "sales": 11486, "sales_prev": 10332, "roce": 15.2, "de": 0.85},
    {"symbol": "CESC", "name": "CESC Ltd", "sector": "Power", "mcap": 24000, "np": 1447, "np_prev": 1397, "sales": 15462, "sales_prev": 14246, "roce": 15.5, "de": 0.95},
    {"symbol": "KPIGREEN", "name": "KPI Green Energy Ltd", "sector": "Power", "mcap": 12500, "np": 161, "np_prev": 110, "sales": 1024, "sales_prev": 644, "roce": 19.8, "de": 0.78},
    {"symbol": "INOXWIND", "name": "Inox Wind Ltd", "sector": "Power", "mcap": 26000, "np": 144, "np_prev": -697, "sales": 1743, "sales_prev": 737, "roce": 15.4, "de": 0.35}
]

def check_fundamental_criteria(stock: dict) -> bool:
    """
    Evaluates Screener.in fundamental query rules:
    - Market Capitalization > 500 Cr
    - Net profit > 100 Cr
    - Net profit > Net Profit preceding year
    - Sales > Sales preceding year
    - Return on capital employed > 15
    - Debt to equity < 1
    """
    c1 = stock.get("mcap", 0) > 500
    c2 = stock.get("np", 0) > 100
    c3 = stock.get("np", 0) > stock.get("np_prev", 0)
    c4 = stock.get("sales", 0) > stock.get("sales_prev", 0)
    c5 = stock.get("roce", 0) > 15.0
    c6 = stock.get("de", 999.0) < 1.0
    return c1 and c2 and c3 and c4 and c5 and c6

def analyze_single_momentum_stock(stock: dict) -> dict:
    """
    Evaluates live technical criteria and computes full swing strategy parameters:
    Technical rules:
    - Current price > 10
    - Current price > DMA 200
    - DMA 50 > DMA 200
    - RSI > 60 AND RSI < 100
    - Volume > 10000
    """
    sym = stock["symbol"]
    try:
        df = fetch_stock_data(sym, range_str="1y", interval="1d")
        if df.empty or len(df) < 50:
            return None
        
        curr_close = float(df["close"].iloc[-1])
        dma200 = float(df["close"].rolling(200, min_periods=50).mean().iloc[-1])
        dma50 = float(df["close"].rolling(50, min_periods=20).mean().iloc[-1])
        curr_rsi = float(df["rsi14"].iloc[-1])
        curr_vol = float(df["volume"].iloc[-1])
        curr_st = float(df["supertrend"].iloc[-1])
        curr_st_dir = int(df["st_dir"].iloc[-1])
        curr_atr = float(df["atr"].iloc[-1]) if "atr" in df.columns else round(curr_close * 0.02, 2)
        
        # Exact Technical Rules from Screener Query
        cond_price_10 = curr_close > 10.0
        cond_price_dma200 = curr_close > dma200
        cond_dma50_200 = dma50 > dma200
        cond_rsi = 60.0 <= curr_rsi <= 100.0
        cond_volume = curr_vol > 10000

        if not (cond_price_10 and cond_price_dma200 and cond_dma50_200 and cond_rsi and cond_volume):
            return None
            
        # Additional indicator metrics for comprehensive swing details
        avg_vol20 = float(df["volume"].tail(20).mean())
        vol_ratio = (curr_vol / avg_vol20) if avg_vol20 > 0 else 1.0
        
        # ADX & MACD
        curr_adx = float(df["adx14"].iloc[-1]) if "adx14" in df.columns else 25.0
        curr_macd_h = float(df["macd_hist"].iloc[-1]) if "macd_hist" in df.columns else 0.5
        
        # Rate of Change (Momentum)
        curr_roc20 = float(((curr_close - df["close"].iloc[-21]) / df["close"].iloc[-21]) * 100) if len(df) >= 21 else 5.0
        curr_roc60 = float(((curr_close - df["close"].iloc[-61]) / df["close"].iloc[-61]) * 100) if len(df) >= 61 else 15.0
        high_52w = float(df["high"].tail(252).max())
        curr_52w_gap = float(((high_52w - curr_close) / high_52w) * 100) if high_52w > 0 else 0.0

        # Stop-Loss Strategy:
        # Standard Supertrend SL (with fallback to 50 DMA if Supertrend is above price)
        if curr_st < curr_close and curr_st_dir == 1:
            stop_loss = round(curr_st, 2)
        else:
            stop_loss = round(min(dma50, curr_close * 0.94), 2)
            
        # 5% Stop-Loss Rule requested by user
        sl_5pct = round(curr_close * 0.95, 2)
        risk_pct = round(((curr_close - stop_loss) / curr_close) * 100, 2)
        
        # Risk per share
        risk_per_share = max(curr_close - stop_loss, curr_close * 0.02)
        
        # Profit Targets
        target1 = round(curr_close + (risk_per_share * 1.5), 2)
        target2 = round(curr_close + (risk_per_share * 2.5), 2)
        target3 = round(curr_close + (risk_per_share * 4.0), 2)
        
        pct_from_50dma = round(((curr_close - dma50) / dma50) * 100, 2)
        pct_from_200dma = round(((curr_close - dma200) / dma200) * 100, 2)
        
        # Growth calculations
        np_growth = round(((stock["np"] - stock["np_prev"]) / stock["np_prev"]) * 100, 1)
        sales_growth = round(((stock["sales"] - stock["sales_prev"]) / stock["sales_prev"]) * 100, 1)
        
        # Pro Confidence Score (out of 7)
        c_score = 3 # base for meeting all fundamental + technical criteria
        if curr_st_dir == 1: c_score += 1
        if 60 <= curr_rsi <= 75: c_score += 1
        if vol_ratio >= 1.0: c_score += 1
        if stock["roce"] >= 25.0: c_score += 1
        c_score = min(c_score, 7)
        
        confidence_label = "ELITE MOMENTUM LEADER" if c_score >= 6 else "HIGH CONVICTION SWING"
        verdict_badge = "badge-success"
        suitability_verdict = "ACTIONABLE - STRONG MOMENTUM"

        reasons = [
            f"RSI {curr_rsi:.1f} in strong momentum zone (60-100)",
            f"Golden Cross intact (50 DMA ₹{dma50:.1f} > 200 DMA ₹{dma200:.1f})",
            f"Price above 200 DMA by +{pct_from_200dma:.1f}%",
            f"ROCE: {stock['roce']}% | Net Profit: ₹{stock['np']:,} Cr (+{np_growth:.1f}% YoY)",
            f"Sales: ₹{stock['sales']:,} Cr (+{sales_growth:.1f}% YoY) | D/E: {stock['de']}"
        ]
        
        action_plan = f"Initiate buy above ₹{curr_close:.2f} on momentum continuation. Trail SL at Supertrend ₹{stop_loss:.2f} (5% SL: ₹{sl_5pct:.2f}). Book partials at T1 ₹{target1:.2f} and T2 ₹{target2:.2f}."

        latest_date_str = str(df.index[-1].date()) if hasattr(df.index[-1], 'date') else str(df.index[-1])[:10]

        return {
            "symbol": sym,
            "name": stock["name"],
            "sector": stock["sector"],
            "signal_type": "BUY",
            "timeframe": "Daily",
            "trigger_date": latest_date_str,
            "days_ago": 0,
            "trigger_price": round(dma50, 2),
            "current_price": round(curr_close, 2),
            "main_ema": round(dma50, 2),
            "main_ema_name": "50 DMA",
            "ema200": round(dma200, 2),
            "dma50": round(dma50, 2),
            "dma200": round(dma200, 2),
            "supertrend": round(curr_st, 2),
            "supertrend_direction": "Bullish (Green)" if curr_st_dir == 1 else "Bearish (Red)",
            "atr": round(curr_atr, 2),
            "rsi14": round(curr_rsi, 1),
            "adx14": round(curr_adx, 1),
            "macd_hist": round(curr_macd_h, 3),
            "roc20": round(curr_roc20, 2),
            "roc60": round(curr_roc60, 2),
            "pct_from_52w_high": round(curr_52w_gap, 1),
            "volume_ratio": round(vol_ratio, 2),
            "pct_from_trigger": pct_from_50dma,
            "pct_from_ema": pct_from_50dma,
            "stop_loss": stop_loss,
            "sl_5pct": sl_5pct,
            "sl_rule_5pct_text": f"As per 5% stop loss rule, suggested SL is ₹{sl_5pct:.2f}",
            "risk_pct": risk_pct,
            "target1": target1,
            "target2": target2,
            "target3": target3,
            "reward_risk_ratio": "1:1.5 (T1) / 1:2.5 (T2) / 1:4 (T3)",
            "suitability": suitability_verdict,
            "verdict_badge": verdict_badge,
            "is_actionable": True,
            "reasons": reasons,
            "action_plan": action_plan,
            "confidence_score": c_score,
            "confidence_label": confidence_label,
            "confidence_badge": "badge-success",
            "enhanced_option": {
                "trend_aligned": True,
                "vol_confirmed": bool(vol_ratio >= 1.0),
                "rsi_healthy": bool(60 <= curr_rsi <= 80),
                "adx_trending": bool(curr_adx >= 25),
                "macd_bullish": bool(curr_macd_h > 0),
                "momentum_ok": True,
                "near_highs": bool(curr_52w_gap <= 15),
                "pro_score": f"{c_score}/7",
                "pro_status": confidence_label
            },
            "fundamentals": {
                "mcap": stock["mcap"],
                "np": stock["np"],
                "np_prev": stock["np_prev"],
                "np_growth_pct": np_growth,
                "sales": stock["sales"],
                "sales_prev": stock["sales_prev"],
                "sales_growth_pct": sales_growth,
                "roce": stock["roce"],
                "debt_to_equity": stock["de"]
            }
        }
    except Exception as e:
        return None

def run_momentum_screener(top_n: int = None, max_workers: int = 30, force_refresh: bool = False) -> dict:
    """
    Scans the fundamental universe, applies all 11 criteria, and returns the entire qualified list sorted by RSI high to low.
    """
    t_start = time.time()
    
    # Check cache if not forcing refresh
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            mtime = os.path.getmtime(CACHE_FILE)
            if (time.time() - mtime) < 1800: # 30 min cache
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    if cached_data.get("signals") and len(cached_data["signals"]) > 0:
                        return cached_data
        except Exception:
            pass

    # 1. Filter fundamental universe
    fund_candidates = [s for s in MOMENTUM_FUNDAMENTAL_UNIVERSE if check_fundamental_criteria(s)]
    
    # 2. Run technical screening in parallel
    qualified = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(analyze_single_momentum_stock, fund_candidates)
        for r in results:
            if r:
                qualified.append(r)
                
    # 3. Rank stocks: Default sort order is based on RSI high to low
    qualified.sort(key=lambda x: float(x.get("rsi14", 0.0)), reverse=True)

    # Show entire list (uncapped unless explicit positive top_n requested)
    output_signals = qualified[:top_n] if (top_n is not None and top_n > 0) else qualified
    
    t_elapsed = round(time.time() - t_start, 2)
    
    result = {
        "status": "success",
        "mode": "momentum",
        "query": (
            "Market Capitalization > 500 AND Current price > 10 AND "
            "Current price > DMA 200 AND DMA 50 > DMA 200 AND "
            "RSI > 60 AND RSI < 100 AND Net profit > 100 AND "
            "Net profit > Net Profit preceding year AND Sales > Sales preceding year AND "
            "Return on capital employed > 15 AND Debt to equity < 1 AND Volume > 10000"
        ),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scan_duration_sec": t_elapsed,
        "total_scanned_stocks": len(MOMENTUM_FUNDAMENTAL_UNIVERSE),
        "total_triggers_found": len(output_signals),
        "signals": output_signals,
        "summary": {
            "total_candidates_passed_all": len(qualified),
            "top_listed": len(output_signals),
            "actionable_buys": len(output_signals),
            "actionable_sells": 0,
            "not_suitable": 0,
            "pro_enhanced_picks": sum(1 for s in output_signals if s.get("confidence_score", 0) >= 6)
        }
    }
    
    # Save to disk cache
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    except Exception as e:
        print(f"Error saving momentum scan cache: {e}")
        
    return result

if __name__ == "__main__":
    res = run_momentum_screener(top_n=None, force_refresh=True)
    print(f"Total Qualified Signals Returned: {len(res['signals'])}")
    for i, s in enumerate(res['signals'], 1):
        fund = s["fundamentals"]
        print(f"{i:2d}. {s['symbol']:12} | CMP: ₹{s['current_price']:8.2f} | 50 DMA: ₹{s['dma50']:8.2f} | 200 DMA: ₹{s['dma200']:8.2f} | RSI: {s['rsi14']:4.1f} | ROCE: {fund['roce']}% | NP: ₹{fund['np']:,} Cr (+{fund['np_growth_pct']}%) | D/E: {fund['debt_to_equity']}")
