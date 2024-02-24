from django.shortcuts import render

# from sheet_api.scraper.scraper import parse_composer


def trigger_scan(request):
    # p = parse_composer("Wolfgang Amadeus Mozart")
    print("Got scan request: ", request)
    p = None
    return render(request, "admin/sheet_api/trigger_scan.html", {"p": p})
