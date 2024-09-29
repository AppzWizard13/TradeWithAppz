from django.shortcuts import render
from django.views import View  


class DashboardView(View):
    def get(self, request , **kwargs):
        #print("pppppppppppppppppppppp")
        template = "trading_tool/html/index.html"
        context={}



        return render(request, template, context)
