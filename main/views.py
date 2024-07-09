from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import UserProfileForm, LoginForm, NewsForm, ContactForm
from .models import News, UserProfile, Slider

def home(request):
    slides = Slider.objects.all()
    latest_news = News.objects.all().order_by('-created_at')[:10]
    return render(request, 'main/home.html', {'slides': slides, 'latest_news': latest_news})


from django.shortcuts import render
from django.db.models import Q
from .models import News, NewsCategory
from .forms import NewsFilterForm
from django.core.paginator import Paginator

def news_list(request):
    news = News.objects.all().order_by('-created_at')
    form = NewsFilterForm(request.GET)
    
    if form.is_valid():
        category = form.cleaned_data.get('category')
        search = form.cleaned_data.get('search')
        
        if category:
            news = news.filter(category=category)
        
        if search:
            news = news.filter(
                Q(title__icontains=search) |
                Q(summary__icontains=search) |
                Q(content__icontains=search) |
                Q(category__name__icontains=search)
            )
    
    paginator = Paginator(news, 10)  # Показывать 10 новостей на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'main/news_list.html', {'page_obj': page_obj, 'form': form})

def news_detail(request, pk):
    news_item = get_object_or_404(News, pk=pk)
    return render(request, 'main/news_detail.html', {'news_item': news_item})

@login_required
@user_passes_test(lambda u: u.is_staff)
def news_create(request):
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user
            news.save()
            return redirect('news_detail', pk=news.pk)
    else:
        form = NewsForm()
    return render(request, 'main/news_form.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_staff)
def news_edit(request, pk):
    news_item = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news_item)
        if form.is_valid():
            form.save()
            return redirect('news_detail', pk=news_item.pk)
    else:
        form = NewsForm(instance=news_item)
    return render(request, 'main/news_form.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_staff)
def news_delete(request, pk):
    news_item = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        news_item.delete()
        return redirect('news_list')
    return render(request, 'main/news_confirm_delete.html', {'news_item': news_item})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'main/login.html', {'form': form})

from .forms import CustomUserCreationForm

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'main/register.html', {'form': form})

@login_required
def profile_view(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    return render(request, 'main/profile.html', {'form': form})


from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from .forms import ContactForm
from .models import ContactMessage
from django.conf import settings

@csrf_protect
def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            # Отправка email
            send_mail(
                subject=f"Новое сообщение от {contact_message.name}",
                message=contact_message.message,
                from_email=contact_message.email,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            return JsonResponse({'message': 'Ваше сообщение успешно отправлено.'}, status=200)
        else:
            return JsonResponse({'message': 'Произошла ошибка при отправке сообщения.'}, status=400)
    return JsonResponse({'message': 'Неверный метод запроса.'}, status=405)
