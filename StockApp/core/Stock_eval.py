import yfinance as yf
import requests
# import math
import os

FMP_API_KEY = os.getenv("FMP_API_KEY")

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


def get_fmp_data(ticker):
    base_url = f"https://financialmodelingprep.com/api/v3/"
    endpoints = {
        "income": f"income-statement/{ticker}?limit=10&apikey={FMP_API_KEY}",
        "balance": f"balance-sheet-statement/{ticker}?limit=10&apikey={FMP_API_KEY}",
        "cashflow": f"cash-flow-statement/{ticker}?limit=10&apikey={FMP_API_KEY}"
    }

    data = {}
    for key, url in endpoints.items():
        res = requests.get(base_url + url)
        if res.status_code == 200:
            data[key] = res.json()
        else:
            print(f"Failed to get {key} data.")
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
        return percent >= 10
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


def rule1_valuation(eps, growth_rate, future_pe, years=10):
    future_eps = eps * ((1 + growth_rate / 100) ** years)
    future_value = future_eps * future_pe
    # divide by 4 for 10 years, 2 for 5 years
    present_value = future_value / (2 ** (years / 5))  

    print("\n[Rule #1 Valuation]")
    print(f"Intrinsic Value: ${round(present_value, 2)}")
    print(f"30% Margin of Safety: ${round(present_value / 1.3, 2)}")


def main(ticker):
    print(f"Checking {ticker}...\n")
    realtime = get_realtime_data(ticker)
    fmp = get_fmp_data(ticker)

    income = fmp["income"]
    balance = fmp["balance"]
    cashflow = fmp["cashflow"]
    print(income,'\n',balance,'\n',cashflow,'\n')


    # Get historical metrics. need to get these from quickfs.
    # change this for my own app later on
    #  

    revenue = [x['revenue'] for x in income if 'revenue' in x]
    eps = [x['epsdiluted'] for x in income if 'epsdiluted' in x]
    equity = [x['totalStockholdersEquity'] for x in balance if 'totalStockholdersEquity' in x]
    fcf = [x['freeCashFlow'] for x in cashflow if 'freeCashFlow' in x]

    print("Checking 10% growth rule...")
    checks = [
        check_growth(revenue, "Revenue"),
        check_growth(eps, "EPS"),
        check_growth(equity, "Equity"),
        check_growth(fcf, "Free Cash Flow")
    ]

    if all(checks):
        print("✅ Passed all growth checks!")
    else:
        print("❌ Failed one or more growth checks.")
        print(f"Revenue : {checks[0]}",'\n')
        print(f"EPS : {checks[1]}",'\n')
        print(f"Equity : {checks[2]}",'\n')
        print(f"Free Cash Flow : {checks[3]}",'\n')
        


    # Run valuations
    FCF = fcf[0] if fcf else 0
    dcf_growth_estimate = 10  # ill pull from somewhere later. for now 10 is ok.
    rule1_growth = 10         # This is the EPS growth rate over 5/10y. 
    future_pe = 15            # conservative  20+ is for aggressive growth companies. run both later on. 
    print("checking dicounted cf numbers",
        FCF,
        dcf_growth_estimate,
        rule1_growth,
        future_pe,
        realtime['shares_outstanding'],
        realtime['cash'],
        realtime['stock_assets'],
        )
    discounted_cf(
        FCF=FCF,
        shares=realtime['shares_outstanding'],
        growth_rate=dcf_growth_estimate,
        cash=realtime['cash'],
        stock= realtime['stock_assets'] or 0 
    )

    rule1_valuation(
        eps=realtime['ttm_eps'],
        growth_rate=rule1_growth,
        future_pe=future_pe
    )


if __name__ == "__main__":
    main("AAPL")

# just checking if the code works individually before applying to web app
