import yfinance as yf
import requests
import time

def get_realtime_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "current_price": info.get("currentPrice"),
        "shares_outstanding": info.get("sharesOutstanding"),
        "ttm_eps": info.get("trailingEps"),
        "cash": info.get("totalCash"),
        "stock_assets": info.get("totalAssets"), 
    }

def get_fmp_data(ticker, api_key):  
    base_url = f"https://financialmodelingprep.com/api/v3/"
    endpoints = {
        "income": f"income-statement/{ticker}?limit=10&apikey={api_key}",
        "balance": f"balance-sheet-statement/{ticker}?limit=10&apikey={api_key}",
        "cashflow": f"cash-flow-statement/{ticker}?limit=10&apikey={api_key}",
        "company_info": f"profile/{ticker}?apikey={api_key}"
    }

    data = {}
    for key, url in endpoints.items():
        res = requests.get(base_url + url)
        if res.status_code == 200:
            data[key] = res.json()
        elif res.status_code == 429:
            print(f"API rate limit reached for {key}. Retrying in 60 seconds...")
            time.sleep(60)  # Sleeping before another retry
            res = requests.get(base_url + url)  
            if res.status_code == 200:
                data[key] = res.json()
            else:
                print(f"Failed to get {key} data after retry.")
                data[key] = []  
        else:
            print(f"Failed to get {key} data. HTTP Status Code: {res.status_code}")
            data[key] = []  

    return data

def calculate_cagr(start, end, years):
    if start <= 0 or end <= 0 or years <= 0:
        return None
    return (end / start) ** (1 / years) - 1

def check_growth(metric_list, label):
    if len(metric_list) < 2:
        print(f"Not enough data to calculate {label} growth.")
        return False

    start = metric_list[-1]
    end = metric_list[0]
    years = len(metric_list) - 1
    growth = calculate_cagr(start, end, years)
    if growth is not None:
        percent = round(growth * 100, 2)
        print(f"{label} CAGR: {percent}%")
        return f"✅ : {round(percent,1)}%" if percent>10 else f"❌ : {round(percent,1)}%"
        # return percent >= 10
    else:
        print(f"Invalid {label} data.")
        return False

def discounted_cf(FCF, shares, growth_rate, cash, stock, years=10, discount_rate=0.15):
    future_value = FCF * (1 + growth_rate / 100) ** years
    discounted = future_value / ((1 + discount_rate) ** years)
    total_value = discounted + cash + stock
    value_per_share = total_value / shares
    print("\n[DCF Valuation]")
    print(f"Intrinsic Value: ${round(value_per_share, 2)}")
    print(f"30% Margin of Safety: ${round(value_per_share / 1.3, 2)}")
    return { 
        "Intrinsic Value": round(value_per_share, 2),
        "30% Margin of Safety": round(value_per_share / 1.3, 2),
        "40% Margin of Safety": round(value_per_share / 1.4, 2),
        "50% Margin of Safety": round(value_per_share / 1.5, 2),
    }

def rule1_valuation(eps, growth_rate, future_pe, years=10):
    future_eps = eps * ((1 + growth_rate / 100) ** years)
    future_value = future_eps * future_pe
    present_value = future_value / (2 ** (years / 5))  

    print("\n[Rule #1 Valuation]")
    print(f"Intrinsic Value: ${round(present_value, 2)}")
    print(f"30% Margin of Safety: ${round(present_value / 1.3, 2)}")
    return { 
        "Intrinsic Value": round(present_value, 2),
        "30% Margin of Safety": round(present_value / 1.3, 2),
        "40% Margin of Safety": round(present_value / 1.4, 2),
        "50% Margin of Safety": round(present_value / 1.5, 2),
    }

def full_stock_evaluation(ticker, api_key):  
    print(f"Checking {ticker}...\n")
    realtime = get_realtime_data(ticker)
    fmp = get_fmp_data(ticker, api_key)
    if not fmp.get('company_info'):
        return False

    income = fmp["income"]
    balance = fmp["balance"]
    cashflow = fmp["cashflow"]
    company_info = {
        "name": fmp['company_info'][0]["companyName"],
        "country": fmp['company_info'][0]['country'],
        "industry": fmp['company_info'][0]["industry"],
        "ceo": fmp['company_info'][0]["ceo"],
    }
    current_price = realtime['current_price']

    # historical metrics
    revenue = [x['revenue'] for x in income if 'revenue' in x]
    eps = [x['epsdiluted'] for x in income if 'epsdiluted' in x]
    equity = [x['totalStockholdersEquity'] for x in balance if 'totalStockholdersEquity' in x]
    fcf = [x['freeCashFlow'] for x in cashflow if 'freeCashFlow' in x]

    print("Checking 10% growth rule...")
    thresholdChecks = {
        "Revenue": check_growth(revenue, "Revenue"),
        "EPS": check_growth(eps, "EPS"),
        "Equity": check_growth(equity, "Equity"),
        "Free Cash Flow": check_growth(fcf, "Free Cash Flow")
    }

    # Run valuations
    FCF = fcf[0] if fcf else 0
    dcf_growth_estimate = 10  
    rule1_growth = 10         
    future_pe = 15            
    print("Checking discounted CF numbers", FCF, dcf_growth_estimate, rule1_growth, future_pe, realtime['shares_outstanding'], realtime['cash'], realtime['stock_assets'])
    DCF_output = discounted_cf(
        FCF=FCF,
        shares=realtime['shares_outstanding'],
        growth_rate=dcf_growth_estimate,
        cash=realtime['cash'],
        stock=realtime['stock_assets'] or 0,
    )

    rule1_output = rule1_valuation(
        eps=realtime['ttm_eps'],
        growth_rate=rule1_growth,
        future_pe=future_pe
    )

    return {
        'company_info': company_info,
        "thresholdChecks": thresholdChecks,
        "DCFOutput": DCF_output,
        "rule1Output": rule1_output,
        'current_price': current_price
    }
