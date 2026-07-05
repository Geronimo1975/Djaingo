from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'index.html', {
        'title': 'AI Wave',
        'subtitle': 'AI Wave'
    }) 
