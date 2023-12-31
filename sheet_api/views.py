from django.shortcuts import render

from sheet_api.scraper import parse_composer


def trigger_scan(request):
    p = parse_composer("Wolfgang Amadeus Mozart")
    return render(request, "sheet_api/trigger_scan.html", {"p": p})
