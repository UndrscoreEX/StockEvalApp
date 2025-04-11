def get_stock_info(code):
    stockProfile = {
        "price" : f'{code} price',
        "pe_ratio" : f'{code} pe'
    }
    return stockProfile