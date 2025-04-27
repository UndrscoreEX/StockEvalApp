from django.shortcuts import render
from django.http import HttpResponse
from .stock_utils import get_stock_info  
from .Stock_eval import full_stock_evaluation


def index(request):
    return render(request, "core/index.html")

def stock_info(request):
    api_key = request.POST.get('api_key')  
    stock_code = request.POST.get('code')  
    data = full_stock_evaluation(stock_code, api_key)
    print(api_key)
    print(data)
    return render(request, "core/_stock_result.html", {"data": data})

