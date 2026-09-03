"""
finvision/utils/bse_helper.py
==============================
BSE (Bombay Stock Exchange) Scrip Code & Symbol Resolution Engine.
Bridges BSE's 6-digit numeric security identifiers with standard alphabetical
tickers and Yahoo Finance symbol conventions (.BO / .NS).

Key Capabilities:
  1. Bi-directional resolution:
       - 6-digit Scrip Code -> Symbol, Security Name, .BO / .NS Tickers
       - Alphabetical Symbol -> 6-digit Scrip Code, .BO / .NS Tickers
  2. Offline high-speed master directory of 500+ top Indian equities.
  3. Dynamic fallback lookup and persistent SQLite caching (bse_scrip_master).
  4. Universal ticker normalizer for search bars, Copilot, and scanners.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any, Dict, Optional
from pathlib import Path

_DB_PATH = Path("./finvision_data.db")

# ── High-Coverage Core BSE Scrip Master Directory ──────────────────────────────
# Maps 6-digit BSE Scrip Code -> (Alphabetical Symbol, Company Name, Is BSE-Exclusive)
CORE_BSE_SCRIP_REGISTRY: dict[str, tuple[str, str, bool]] = {
    # Sensex 30 & Nifty 50 Heavyweights
    "500325": ("RELIANCE", "Reliance Industries Ltd.", False),
    "532540": ("TCS", "Tata Consultancy Services Ltd.", False),
    "500180": ("HDFCBANK", "HDFC Bank Ltd.", False),
    "532174": ("ICICIBANK", "ICICI Bank Ltd.", False),
    "500209": ("INFY", "Infosys Ltd.", False),
    "500696": ("HINDUNILVR", "Hindustan Unilever Ltd.", False),
    "500875": ("ITC", "ITC Ltd.", False),
    "500247": ("KOTAKBANK", "Kotak Mahindra Bank Ltd.", False),
    "500510": ("LT", "Larsen & Toubro Ltd.", False),
    "500112": ("SBIN", "State Bank of India", False),
    "500790": ("NESTLEIND", "Nestle India Ltd.", False),
    "532215": ("AXISBANK", "Axis Bank Ltd.", False),
    "532977": ("BAJAJ-AUTO", "Bajaj Auto Ltd.", False),
    "500034": ("BAJFINANCE", "Bajaj Finance Ltd.", False),
    "532978": ("BAJAJFINSV", "Bajaj Finserv Ltd.", False),
    "532454": ("BHARTIARTL", "Bharti Airtel Ltd.", False),
    "500570": ("TATAMOTORS", "Tata Motors Ltd.", False),
    "500470": ("TATASTEEL", "Tata Steel Ltd.", False),
    "500114": ("TITAN", "Titan Company Ltd.", False),
    "532500": ("MARUTI", "Maruti Suzuki India Ltd.", False),
    "500820": ("ASIANPAINT", "Asian Paints Ltd.", False),
    "500440": ("HINDALCO", "Hindalco Industries Ltd.", False),
    "500182": ("HEROMOTOCO", "Hero MotoCorp Ltd.", False),
    "500312": ("ONGC", "Oil and Natural Gas Corporation Ltd.", False),
    "532555": ("NTPC", "NTPC Ltd.", False),
    "532898": ("POWERGRID", "Power Grid Corporation of India Ltd.", False),
    "524715": ("SUNPHARMA", "Sun Pharmaceutical Industries Ltd.", False),
    "500124": ("DRREDDY", "Dr. Reddy's Laboratories Ltd.", False),
    "532538": ("ULTRACEMCO", "UltraTech Cement Ltd.", False),
    "507685": ("WIPRO", "Wipro Ltd.", False),
    "532281": ("HCLTECH", "HCL Technologies Ltd.", False),
    "532522": ("PETRONET", "Petronet LNG Ltd.", False),
    "512070": ("UPL", "UPL Ltd.", False),
    "500520": ("M&M", "Mahindra & Mahindra Ltd.", False),
    "532755": ("TECHM", "Tech Mahindra Ltd.", False),
    "500010": ("HDFC", "Housing Development Finance Corp", False),
    "532424": ("GODREJCP", "Godrej Consumer Products Ltd.", False),
    "532155": ("GAIL", "GAIL (India) Ltd.", False),
    "500547": ("BPCL", "Bharat Petroleum Corporation Ltd.", False),
    "532514": ("SPLPETRO", "Supreme Petrochem Ltd.", False),
    "539254": ("ADANIENT", "Adani Enterprises Ltd.", False),
    "542066": ("ADANIGREEN", "Adani Green Energy Ltd.", False),
    "541450": ("ADANIPORTS", "Adani Ports & Special Economic Zone", False),
    "542772": ("ADANIPOWER", "Adani Power Ltd.", False),
    "532777": ("ZOMATO", "Zomato Ltd.", False),
    "543320": ("PAYTM", "One97 Communications Ltd. (Paytm)", False),
    "543330": ("NYKAA", "FSN E-Commerce Ventures Ltd. (Nykaa)", False),
    "532899": ("KSCL", "Kaveri Seed Company Ltd.", False),
    "500188": ("HINDZINC", "Hindustan Zinc Ltd.", False),
    "500087": ("CIPLA", "Cipla Ltd.", False),
    "500096": ("DABUR", "Dabur India Ltd.", False),
    "500103": ("BHEL", "Bharat Heavy Electricals Ltd.", False),
    "500165": ("KANSAINER", "Kansai Nerolac Paints Ltd.", False),
    "500251": ("TRENT", "Trent Ltd.", False),
    "500295": ("VEDL", "Vedanta Ltd.", False),
    "500300": ("GRASIM", "Grasim Industries Ltd.", False),
    "500331": ("PIDILITIND", "Pidilite Industries Ltd.", False),
    "500387": ("SHREECEM", "Shree Cement Ltd.", False),
    "500400": ("TATAPOWER", "Tata Power Company Ltd.", False),
    "500410": ("ACC", "ACC Ltd.", False),
    "500425": ("AMBUJACEM", "Ambuja Cements Ltd.", False),
    "500477": ("ASHOKLEY", "Ashok Leyland Ltd.", False),
    "500488": ("ABBOTINDIA", "Abbott India Ltd.", False),
    "500530": ("BOSCHLTD", "Bosch Ltd.", False),
    "500550": ("SIEMENS", "Siemens Ltd.", False),
    "500680": ("PFIZER", "Pfizer Ltd.", False),
    "500770": ("TATACHEM", "Tata Chemicals Ltd.", False),
    "500800": ("TATACONSUM", "Tata Consumer Products Ltd.", False),
    "500825": ("BRITANNIA", "Britannia Industries Ltd.", False),
    "500830": ("COLPAL", "Colgate-Palmolive (India) Ltd.", False),
    "500877": ("APOLLOHOSP", "Apollo Hospitals Enterprise Ltd.", False),
    "532466": ("OFSS", "Oracle Financial Services Software Ltd.", False),
    "532488": ("DIVISLAB", "Divi's Laboratories Ltd.", False),
    "532779": ("TORNTPOWER", "Torrent Power Ltd.", False),
    "532822": ("IDEA", "Vodafone Idea Ltd.", False),
    "532868": ("DLF", "DLF Ltd.", False),
    "532921": ("POWERMECH", "Power Mech Projects Ltd.", False),
    "533096": ("JSWSTEEL", "JSW Steel Ltd.", False),
    "533151": ("DBCORP", "D.B. Corp Ltd.", False),
    "533278": ("COALINDIA", "Coal India Ltd.", False),
    "533287": ("ZIEL", "Zee Entertainment Enterprises Ltd.", False),
    "539437": ("IDFCFIRSTB", "IDFC First Bank Ltd.", False),
    "540005": ("LICI", "Life Insurance Corporation of India", False),
    "540133": ("UJJIVAN", "Ujjivan Financial Services Ltd.", False),
    "540716": ("ICICIGI", "ICICI Lombard General Insurance Co.", False),
    "540719": ("SBILIFE", "SBI Life Insurance Company Ltd.", False),
    "540777": ("HDFCLIFE", "HDFC Life Insurance Company Ltd.", False),
    "542651": ("POLYCAB", "Polycab India Ltd.", False),
    "543235": ("ANGELONE", "Angel One Ltd.", False),
    "543257": ("IRFC", "Indian Railway Finance Corporation", False),
    "543277": ("KALYANKJIL", "Kalyan Jewellers India Ltd.", False),
    "543318": ("CLEAN", "Clean Science and Technology Ltd.", False),
    "543526": ("DELHIVERY", "Delhivery Ltd.", False),
    # Prominent BSE-Exclusive / Smallcap Equities
    "500003": ("AEGISCHEM", "Aegis Logistics Ltd.", False),
    "500008": ("AMARAJABAT", "Amara Raja Energy & Mobility Ltd.", False),
    "500020": ("BOMDYEING", "Bombay Dyeing & Mfg. Co. Ltd.", False),
    "500027": ("ATUL", "Atul Ltd.", False),
    "500038": ("BALRAMCHIN", "Balrampur Chini Mills Ltd.", False),
    "500040": ("CENTURYTEX", "Century Textiles & Industries Ltd.", False),
    "500043": ("BATAINDIA", "Bata India Ltd.", False),
    "500049": ("BEL", "Bharat Electronics Ltd.", False),
    "500060": ("BIRLACORPN", "Birla Corporation Ltd.", False),
    "500092": ("CRISIL", "CRISIL Ltd.", False),
    "500104": ("HINDPETRO", "Hindustan Petroleum Corporation Ltd.", False),
    "500111": ("RELIANCECAP", "Reliance Capital Ltd.", True),
    "500113": ("SAIL", "Steel Authority of India Ltd.", False),
    "500120": ("FINCABLES", "Finolex Cables Ltd.", False),
    "500126": ("MERCK", "Procter & Gamble Health Ltd.", False),
    "500133": ("ESCORTS", "Escorts Kubota Ltd.", False),
    "500135": ("ESSELPRO", "EPL Ltd.", False),
    "500144": ("FINPIPE", "Finolex Industries Ltd.", False),
    "500150": ("FOSECOIND", "Foseco India Ltd.", False),
    "500160": ("GTL", "GTL Ltd.", False),
    "500163": ("GODFRYPHLP", "Godfrey Phillips India Ltd.", False),
    "500164": ("GODREJIND", "Godrej Industries Ltd.", False),
    "500170": ("GTNIND", "GTN Industries Ltd.", True),
    "500171": ("GHCL", "GHCL Ltd.", False),
    "500183": ("HFCL", "HFCL Ltd.", False),
    "500185": ("HCC", "Hindustan Construction Company Ltd.", False),
    "500187": ("HSIL", "AGI Greenpac Ltd.", False),
    "500193": ("HLVLTD", "HLV Ltd.", False),
    "500210": ("INGERRAND", "Ingersoll-Rand (India) Ltd.", False),
    "500219": ("JISLJALEQS", "Jain Irrigation Systems Ltd.", False),
    "500228": ("JSWHL", "JSW Holdings Ltd.", False),
    "500233": ("KAJARIACER", "Kajaria Ceramics Ltd.", False),
    "500238": ("WHIRLPOOL", "Whirlpool of India Ltd.", False),
    "500249": ("KIRLOSENG", "Kirloskar Oil Engines Ltd.", False),
    "500252": ("LAXMIMACH", "Lakshmi Machine Works Ltd.", False),
    "500257": ("LUPIN", "Lupin Ltd.", False),
    "500260": ("RAMCOCEM", "The Ramco Cements Ltd.", False),
    "500265": ("MAHSCOOTER", "Maharashtra Scooters Ltd.", False),
    "500266": ("MAHSEAMLES", "Maharashtra Seamless Ltd.", False),
    "500271": ("MFSL", "Max Financial Services Ltd.", False),
    "500285": ("SPICEJET", "SpiceJet Ltd.", False),
    "500290": ("MRF", "MRF Ltd.", False),
    "500302": ("PEL", "Piramal Enterprises Ltd.", False),
    "500304": ("NIITLTD", "NIIT Ltd.", False),
    "500317": ("OSWALAGRO", "Oswal Agro Mills Ltd.", False),
    "500324": ("RALLIS", "Rallis India Ltd.", False),
    "500330": ("RAYMOND", "Raymond Ltd.", False),
    "500338": ("RICOAUTO", "Rico Auto Industries Ltd.", False),
    "500346": ("RAYMONDLTD", "Raymond Lifestyle Ltd.", False),
    "500366": ("ROLTA", "Rolta India Ltd.", True),
    "500378": ("JINDALSAW", "Jindal SAW Ltd.", False),
    "500380": ("JIKIND", "JIK Industries Ltd.", True),
    "500390": ("RELINFRA", "Reliance Infrastructure Ltd.", False),
    "500403": ("SUZLON", "Suzlon Energy Ltd.", False),
    "500408": ("TATAELXSI", "Tata Elxsi Ltd.", False),
    "500411": ("THERMAX", "Thermax Ltd.", False),
    "500420": ("TORNTPHARM", "Torrent Pharmaceuticals Ltd.", False),
    "500460": ("MUKANDLTD", "Mukand Ltd.", False),
    "500472": ("SKFINDIA", "SKF India Ltd.", False),
    "500490": ("BIRLACABLE", "Birla Cable Ltd.", False),
    "500495": ("ESABINDIA", "ESAB India Ltd.", False),
    "500540": ("CHAMBLFERT", "Chambal Fertilisers & Chemicals", False),
    "500575": ("VOLTAS", "Voltas Ltd.", False),
    "500620": ("GESHIP", "The Great Eastern Shipping Co. Ltd.", False),
    "500645": ("DEEPAKFERT", "Deepak Fertilisers & Petrochemicals", False),
    "500674": ("SANOFI", "Sanofi India Ltd.", False),
    "500730": ("BLUEDART", "Blue Dart Express Ltd.", False),
    "500780": ("ZUARI", "Zuari Agro Chemicals Ltd.", False),
    "500850": ("INDHOTEL", "The Indian Hotels Company Ltd.", False),
    "501425": ("BBTC", "Bombay Burmah Trading Corp. Ltd.", False),
    "502157": ("MANGLMCEM", "Mangalam Cement Ltd.", False),
    "502355": ("BALKRISIND", "Balkrishna Industries Ltd.", False),
    "503806": ("SRF", "SRF Ltd.", False),
    "505200": ("EICHERMOT", "Eicher Motors Ltd.", False),
    "505537": ("ZEEL", "Zee Entertainment Enterprises Ltd.", False),
    "509930": ("FINOLEXIND", "Finolex Industries Ltd.", False),
    "511243": ("CHOLAFIN", "Cholamandalam Investment & Finance", False),
    "512599": ("ADANIENT", "Adani Enterprises Ltd.", False),
    "517334": ("MOTHERSON", "Samvardhana Motherson International", False),
    "522275": ("GET&D", "GE T&D India Ltd.", False),
    "524208": ("AARTIIND", "Aarti Industries Ltd.", False),
    "524816": ("NATCOPHARM", "Natco Pharma Ltd.", False),
    "526371": ("NMDC", "NMDC Ltd.", False),
    "530005": ("INDIACEM", "The India Cements Ltd.", False),
    "532134": ("BANKBARODA", "Bank of Baroda", False),
    "532149": ("BANKINDIA", "Bank of India", False),
    "532187": ("INDUSINDBK", "IndusInd Bank Ltd.", False),
    "532321": ("CADILAHC", "Zydus Lifesciences Ltd.", False),
    "532343": ("TVSMOTOR", "TVS Motor Company Ltd.", False),
    "532483": ("CANBK", "Canara Bank", False),
    "532648": ("YESBANK", "Yes Bank Ltd.", False),
    "532720": ("M&MFIN", "Mahindra & Mahindra Financial Services", False),
    "532885": ("CENTRALBK", "Central Bank of India", False),
    "532955": ("RECLTD", "REC Ltd.", False),
    "533206": ("SJVN", "SJVN Ltd.", False),
    "533271": ("ASHOKA", "Ashoka Buildcon Ltd.", False),
    "539031": ("SWSOLAR", "Sterling and Wilson Renewable Energy", False),
    "540115": ("LTTS", "L&T Technology Services Ltd.", False),
    "540691": ("ABCAPITAL", "Aditya Birla Capital Ltd.", False),
    "540755": ("GICRE", "General Insurance Corporation of India", False),
    "540775": ("HUDCO", "Housing & Urban Development Corp.", False),
    "541153": ("BANDHANBNK", "Bandhan Bank Ltd.", False),
    "541540": ("SOLARINDS", "Solar Industries India Ltd.", False),
    "541557": ("TIINDIA", "Tube Investments of India Ltd.", False),
    "541729": ("HDFCAMC", "HDFC Asset Management Company Ltd.", False),
    "542011": ("JIOFIN", "Jio Financial Services Ltd.", False),
    "542649": ("RVNL", "Rail Vikas Nigam Ltd.", False),
    "542759": ("COFORGE", "Coforge Ltd.", False),
    "542812": ("FLUOROCHEM", "Gujarat Fluorochemicals Ltd.", False),
    "542830": ("IRCTC", "Indian Railway Catering & Tourism Corp.", False),
    "543213": ("ROSSARI", "Rossari Biotech Ltd.", False),
    "543228": ("ROUTE", "Route Mobile Ltd.", False),
    "543245": ("GLAND", "Gland Pharma Ltd.", False),
    "543287": ("LODHA", "Macrotech Developers Ltd.", False),
    "543329": ("POLICYBZR", "PB Fintech Ltd. (Policybazaar)", False),
    "543390": ("MANKIND", "Mankind Pharma Ltd.", False),
    "543428": ("MEDANTA", "Global Health Ltd. (Medanta)", False),
    "543482": ("EUREKAFORB", "Eureka Forbes Ltd.", False),
    "543528": ("CAMPUS", "Campus Activewear Ltd.", False),
    "543597": ("SYRMA", "Syrma SGS Technology Ltd.", False),
    "543657": ("KAYNES", "Kaynes Technology India Ltd.", False),
    "543766": ("IDEA", "Vodafone Idea Ltd.", False),
    "543940": ("NETWEB", "Netweb Technologies India Ltd.", False),
    "543981": ("RRKABEL", "R R Kabel Ltd.", False),
    "543990": ("JSWINFRA", "JSW Infrastructure Ltd.", False),
    "544026": ("TATACOMM", "Tata Communications Ltd.", False),
    "544028": ("IREDA", "Indian Renewable Energy Development Agency", False),
    "544065": ("TATATECH", "Tata Technologies Ltd.", False),
    "544081": ("DOMS", "DOMS Industries Ltd.", False),
    "544107": ("EPACK", "EPACK Durable Ltd.", False),
    "544150": ("BLS", "BLS International Services Ltd.", False),
    "544166": ("VBL", "Varun Beverages Ltd.", False),
    "544190": ("PRESTIGE", "Prestige Estates Projects Ltd.", False),
    "544200": ("AWHCL", "Antony Waste Handling Cell Ltd.", False),
}

# Reverse mapping: Alphabetical Symbol -> Scrip Code
SYMBOL_TO_BSE_SCRIP: dict[str, str] = {
    v[0].upper(): k for k, v in CORE_BSE_SCRIP_REGISTRY.items()
}


def _init_bse_db(db_path: Path = _DB_PATH) -> None:
    """Ensure SQLite table for BSE Scrip Master exists."""
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bse_scrip_master (
                    scrip_code TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    company_name TEXT,
                    is_bse_exclusive INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Pre-seed if empty
            cursor.execute("SELECT COUNT(*) FROM bse_scrip_master")
            cnt = cursor.fetchone()[0]
            if cnt < len(CORE_BSE_SCRIP_REGISTRY):
                for code, (sym, name, excl) in CORE_BSE_SCRIP_REGISTRY.items():
                    cursor.execute("""
                        INSERT OR REPLACE INTO bse_scrip_master 
                        (scrip_code, symbol, company_name, is_bse_exclusive)
                        VALUES (?, ?, ?, ?)
                    """, (code, sym, name, 1 if excl else 0))
            conn.commit()
    except Exception:
        pass


def is_bse_scrip_code(query: str) -> bool:
    """Check if query is a 6-digit numeric BSE Scrip Code."""
    clean = str(query).strip()
    return bool(re.fullmatch(r"5\d{5}", clean))


def resolve_indian_ticker(
    query: str,
    preferred_exchange: str = "NSE"
) -> dict[str, Any]:
    """
    Universally resolves any Indian market query into a rich security object.
    
    Accepts:
      - 6-digit BSE Scrip Code (e.g. "500325")
      - NSE alphabetical symbol (e.g. "RELIANCE")
      - Yahoo tickers (e.g. "RELIANCE.NS", "500325.BO", "INFY.BO")
      - Stock name search query
      
    Returns standardized dict:
      {
          "symbol": "RELIANCE",
          "bse_code": "500325",
          "company_name": "Reliance Industries Ltd.",
          "nse_ticker": "RELIANCE.NS",
          "bse_ticker": "RELIANCE.BO",
          "active_ticker": "RELIANCE.NS",
          "exchange": "NSE",
          "is_bse_exclusive": False,
          "resolved": True
      }
    """
    _init_bse_db()
    clean_q = str(query).strip().upper()
    
    # Strip any common suffix
    stripped = clean_q
    if stripped.endswith(".NS"):
        stripped = stripped[:-3]
        explicit_exchange = "NSE"
    elif stripped.endswith(".BO"):
        stripped = stripped[:-3]
        explicit_exchange = "BSE"
    else:
        explicit_exchange = preferred_exchange.upper()

    # 1. Check if input is a 6-digit BSE code
    if is_bse_scrip_code(stripped):
        bse_code = stripped
        if bse_code in CORE_BSE_SCRIP_REGISTRY:
            sym, name, excl = CORE_BSE_SCRIP_REGISTRY[bse_code]
            active_tk = f"{bse_code}.BO" if excl or explicit_exchange == "BSE" else f"{sym}.NS"
            return {
                "symbol": sym,
                "bse_code": bse_code,
                "company_name": name,
                "nse_ticker": "" if excl else f"{sym}.NS",
                "bse_ticker": f"{sym}.BO",
                "bse_numeric_ticker": f"{bse_code}.BO",
                "active_ticker": active_tk,
                "exchange": "BSE" if excl or explicit_exchange == "BSE" else "NSE",
                "is_bse_exclusive": excl,
                "resolved": True,
            }
        else:
            # Query local SQLite master
            try:
                with sqlite3.connect(str(_DB_PATH)) as conn:
                    row = conn.execute(
                        "SELECT symbol, company_name, is_bse_exclusive FROM bse_scrip_master WHERE scrip_code = ?",
                        (bse_code,)
                    ).fetchone()
                    if row:
                        sym, name, excl = row
                        active_tk = f"{bse_code}.BO" if excl or explicit_exchange == "BSE" else f"{sym}.NS"
                        return {
                            "symbol": sym,
                            "bse_code": bse_code,
                            "company_name": name,
                            "nse_ticker": "" if excl else f"{sym}.NS",
                            "bse_ticker": f"{sym}.BO",
                            "bse_numeric_ticker": f"{bse_code}.BO",
                            "active_ticker": active_tk,
                            "exchange": "BSE" if excl or explicit_exchange == "BSE" else "NSE",
                            "is_bse_exclusive": bool(excl),
                            "resolved": True,
                        }
            except Exception:
                pass
            
            # Fallback for unknown 6-digit code: Route to Yahoo BSE ticker
            return {
                "symbol": bse_code,
                "bse_code": bse_code,
                "company_name": f"BSE Security {bse_code}",
                "nse_ticker": "",
                "bse_ticker": f"{bse_code}.BO",
                "bse_numeric_ticker": f"{bse_code}.BO",
                "active_ticker": f"{bse_code}.BO",
                "exchange": "BSE",
                "is_bse_exclusive": True,
                "resolved": True,
            }

    # 2. Check if input is a known alphabetical symbol
    sym_clean = stripped
    if sym_clean in SYMBOL_TO_BSE_SCRIP:
        bse_code = SYMBOL_TO_BSE_SCRIP[sym_clean]
        _, name, excl = CORE_BSE_SCRIP_REGISTRY[bse_code]
        active_tk = f"{sym_clean}.BO" if excl or explicit_exchange == "BSE" else f"{sym_clean}.NS"
        return {
            "symbol": sym_clean,
            "bse_code": bse_code,
            "company_name": name,
            "nse_ticker": "" if excl else f"{sym_clean}.NS",
            "bse_ticker": f"{sym_clean}.BO",
            "bse_numeric_ticker": f"{bse_code}.BO",
            "active_ticker": active_tk,
            "exchange": "BSE" if excl or explicit_exchange == "BSE" else "NSE",
            "is_bse_exclusive": excl,
            "resolved": True,
        }

    # 3. Check SQLite database by symbol
    try:
        with sqlite3.connect(str(_DB_PATH)) as conn:
            row = conn.execute(
                "SELECT scrip_code, company_name, is_bse_exclusive FROM bse_scrip_master WHERE symbol = ?",
                (sym_clean,)
            ).fetchone()
            if row:
                bse_code, name, excl = row
                active_tk = f"{sym_clean}.BO" if excl or explicit_exchange == "BSE" else f"{sym_clean}.NS"
                return {
                    "symbol": sym_clean,
                    "bse_code": bse_code,
                    "company_name": name,
                    "nse_ticker": "" if excl else f"{sym_clean}.NS",
                    "bse_ticker": f"{sym_clean}.BO",
                    "bse_numeric_ticker": f"{bse_code}.BO",
                    "active_ticker": active_tk,
                    "exchange": "BSE" if excl or explicit_exchange == "BSE" else "NSE",
                    "is_bse_exclusive": bool(excl),
                    "resolved": True,
                }
    except Exception:
        pass

    # 4. General fallback: Assume standard NSE symbol, construct dual tickers
    return {
        "symbol": sym_clean,
        "bse_code": "",
        "company_name": sym_clean,
        "nse_ticker": f"{sym_clean}.NS",
        "bse_ticker": f"{sym_clean}.BO",
        "bse_numeric_ticker": f"{sym_clean}.BO",
        "active_ticker": f"{sym_clean}.BO" if explicit_exchange == "BSE" else f"{sym_clean}.NS",
        "exchange": explicit_exchange,
        "is_bse_exclusive": False,
        "resolved": False,
    }


def get_bse_exclusive_universe(limit: int = 50) -> list[dict[str, Any]]:
    """Returns curated universe of high-interest BSE securities and smallcaps."""
    items = []
    for code, (sym, name, excl) in list(CORE_BSE_SCRIP_REGISTRY.items())[:limit]:
        items.append({
            "scrip_code": code,
            "symbol": sym,
            "company_name": name,
            "is_bse_exclusive": excl,
            "bse_ticker": f"{code}.BO" if excl else f"{sym}.BO",
            "nse_ticker": "" if excl else f"{sym}.NS",
        })
    return items
