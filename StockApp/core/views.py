from django.shortcuts import render
from django.http import HttpResponse
from .stock_utils import get_stock_info  
from .Stock_eval import full_stock_evaluation


def index(request):
    return render(request, "core/index.html")

def stock_info(request):
    
    code = request.POST.get("code")
    # data = get_stock_info(code)
    data = full_stock_evaluation(code)
    return render(request, "core/_stock_result.html", {"data": data})
