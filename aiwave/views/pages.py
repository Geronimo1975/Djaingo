from django.shortcuts import render, redirect
import json
from wowdash_app.utils import log_error_to_file, log_and_redirect_to_error_page
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from Bal.aiwave.pages import (
    get_team_data_bal,
    get_content_data_bal,
    get_blog_list_data_bal,
    get_blog_detail_data_bal,
    create_blog_post_bal,
    get_chat_export_data_bal,
    export_chat_sessions_bal,
    get_active_sessions_data_bal,
    terminate_user_session_bal,
    terminate_all_other_sessions_bal,
    get_release_notes_data_bal,
    get_help_faq_data_bal,
    process_help_contact_bal,
    update_user_profile_bal,
    delete_blog_post_bal,
)
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.models import User
import markdown


def pricing(request):
    return render(request, 'pages/pricing.html', {
        'title': 'Pricing',
        'subtitle': 'AI Wave'
    })  

def contact(request):
    return render(request, 'pages/contact.html', {
        'title': 'Contact',
        'subtitle': 'AI Wave'
    })  

def team(request):
    try:
        team_members = get_team_data_bal()
    except Exception as e:
        return log_and_redirect_to_error_page(e)
    
    return render(request, 'pages/team.html', {
            'title': 'Our Team',
            'subtitle': 'Meet Our Team',
            'all_members': team_members
        })

def terms(request):
    try:
        terms_content = get_content_data_bal('terms_conditions')
    except Exception as e:
        return log_and_redirect_to_error_page(e)
    
    return render(request, 'pages/termsPolicy.html', {
            'title': 'Terms & Conditions',
            'subtitle': 'AI Wave',
            'terms_content': terms_content
        })

def privacy(request):
    try:
        privacy_content = get_content_data_bal('privacy_conditions')
    except Exception as e:
        return log_and_redirect_to_error_page(e)
    
    return render(request, 'pages/privacyPolicy.html', {
            'title': 'Privacy Policy',
            'subtitle': 'AI Wave',
            'privacy_content': privacy_content
        })


def profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        try:
            full_name = request.POST.get('name')
            email = request.POST.get('email')
            username = request.POST.get('username')
            profile_picture = request.FILES.get('imageUpload')
            
            update_user_profile_bal(request.user, full_name, email, profile_picture, username)
            return redirect('aiwave-profile-details')
        except Exception as e:
            return log_and_redirect_to_error_page(e)
    
    return render(request, 'pages/profileDetails.html', {
        'title': 'View Profile',
        'subtitle': 'View Profile',
        'script': 'js\custom\pages\customProfileDetails.js',
        'profile': profile,
        'user': request.user,
    })

def blog(request):
    """View for listing all blog posts"""
    try:
        search_query = request.GET.get('search', '').strip()
        category = request.GET.get('category', '')
        page = request.GET.get('page')
        
        context = get_blog_list_data_bal(search_query, category, page)
    except Exception as e:
        return log_and_redirect_to_error_page(e)
    
    return render(request, 'pages/blog.html', {
        'script': 'js/custom/pages/customBlog.js',
        'custom_css': 'css/custom/pages/customBlog.css',
        **context
    })

def blogDetails(request, slug):
    """View for displaying a single blog post"""
    try:
        context = get_blog_detail_data_bal(slug)
        # Convert markdown content to HTML if present
        if 'post' in context and hasattr(context['post'], 'content'):
            context['post'].html_content = markdown.markdown(context['post'].content)
    except Exception as e:
        return log_and_redirect_to_error_page(e)
    
    return render(request, 'pages/blogDetails.html', {
        'script': 'js/custom/pages/customBlogDetails.js',
        'custom_css': 'css/custom/pages/customBlogDetails.css',
        **context
        })

@login_required
def createBlog(request):
    """View for creating a new blog post"""
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            content = request.POST.get('content')
            excerpt = request.POST.get('excerpt')
            category = request.POST.get('category')
            tags_input = request.POST.get('tags', '')
            featured_image = request.FILES.get('featured_image')
            
            # Process tags - split by comma and clean
            tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            
            # Create the blog post
            blog = create_blog_post_bal(
                title=title,
                content=content,
                excerpt=excerpt,
                category=category,
                tags=','.join(tags),  # Convert back to string for backward compatibility
                featured_image=featured_image,
                author=request.user
            )
            
            return redirect('aiwave-blog-details', slug=blog.slug)
            
        except Exception as e:
            return log_error_to_file(e)
    
    # Clear any existing messages when just viewing the form
    storage = messages.get_messages(request)
    storage.used = True
    
    return render(request, 'pages/createBlog.html', {
        'custom_css': 'css/custom/pages/customCreateBlog.css',
        'script': 'js/custom/pages/customCreateBlog.js',
    })

def chatExports(request):
    if not request.user.is_authenticated:
        return redirect('aiwave-signin')
    
    try:
        bot_modes = get_chat_export_data_bal(request.user)
    except Exception as e:
        return log_and_redirect_to_error_page(e)
    
    return render(request, 'pages/chatExports.html', {
            'title': 'Chat Export',
            'subtitle': 'Export your chat conversations',
            'script': 'js/custom/pages/customChatExports.js',
            'bot_modes': bot_modes
        })

@login_required
@require_http_methods(['POST'])
def exportChatSessions(request):
    """Export selected chat sessions"""
    try:
        session_ids = request.POST.getlist('session_ids[]')
        if not session_ids:
            return JsonResponse({
                'status': 'error',
                'message': 'No sessions selected'
            }, status=400)

        export_data = export_chat_sessions_bal(session_ids, request.user)

        return JsonResponse({
            'status': 'success',
            'data': export_data
        })
    except Exception as e:
        log_error_to_file(e)
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred.'
        }, status=500)

def plansBilling(request):
    try:
        # Get FAQ data for the pricing page
        faq_data = get_help_faq_data_bal()
    except Exception as e:
        return log_and_redirect_to_error_page(e)
    
    return render(request, 'pages/plansBilling.html', {
            'title': 'Plans & Billing',
            'subtitle': 'AI Wave',
            'faq_categories': faq_data['faq_categories'],
            'faqs_by_category': faq_data['faqs_by_category'],
        })

@login_required
def sessionsPage(request):
    """Render the sessions management page"""
    return render(request, 'pages/sessions.html', {
        'title': 'Active Sessions',
        'subtitle': 'Manage your active sessions',
        'script': 'js\custom\pages\customSessions.js',
    })

@login_required
def getActiveSessions(request):
    """Get all active sessions for the current user"""
    try:
        sessions_data = get_active_sessions_data_bal(request.user, request.session.session_key)
        
        return JsonResponse({
            'status': 'success',
            'sessions': sessions_data
        })
    except Exception as e:
        log_error_to_file(e)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
@require_http_methods(['POST'])
def terminateSession(request):
    """Terminate a specific session"""
    try:
        session_id = request.POST.get('session_id')
        if not session_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Session ID is required'
            }, status=400)

        terminate_user_session_bal(session_id, request.user, request.session.session_key)

        return JsonResponse({
            'status': 'success',
            'message': 'Session terminated successfully'
        })
    except Exception as e:
        log_error_to_file(e)
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred.'
        }, status=500)

@login_required
@require_http_methods(['POST'])
def terminateAllSessions(request):
    """Terminate all sessions except the current one"""
    try:
        terminate_all_other_sessions_bal(request.user, request.session.session_key)

        return JsonResponse({
            'status': 'success',
            'message': 'All other sessions terminated successfully'
        })
    except Exception as e:
        log_error_to_file(e)
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred.'
        }, status=500)

def releaseNotes(request):
    try:
        release_notes = get_release_notes_data_bal()
    except Exception as e:
        return log_and_redirect_to_error_page(e)
    
    return render(request, 'pages/releaseNotes.html', {
            'title': 'Release Notes',
            'subtitle': 'Release Notes',
            'release_notes': release_notes
        })



def help(request):
    try:
        help_data = get_help_faq_data_bal()
        
        if request.method == 'POST':
            name = request.POST.get('name')
            email = request.POST.get('email')
            subject = request.POST.get('subject')
            phone = request.POST.get('phone')
            message = request.POST.get('message')

            try:
                process_help_contact_bal(name, email, subject, phone, message)
                return redirect('aiwave-contact')
            except Exception as e:
                log_error_to_file(e)

    except Exception as e:
        return log_and_redirect_to_error_page(e)
    
    return render(request, 'pages/help.html', {
            'title': 'Help & FAQ',
            'subtitle': 'Help & FAQ',
            'custom_css': 'css/custom/pages/customHelp.css',
            'script': 'js/custom/pages/customHelp.js',
            'faq_categories': help_data['faq_categories'],
            'faqs_by_category': help_data['faqs_by_category'],
        })


@login_required
@require_http_methods(["POST"])
def deleteBlog(request, pk):
    """Delete a blog post if the user is the author"""
    delete_blog_post_bal(pk, request.user)
    
    return redirect(reverse('aiwave-blog'))

@csrf_exempt
def n8n_create_blog(request):
    """Endpoint for n8n HTTP node to create a blog post automatically."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        title = data.get('title')
        content = data.get('content')
        excerpt = data.get('excerpt', '')
        category = data.get('category', '')
        tags = data.get('tags', '')
        author_username = data.get('author_username')
        featured_image = request.FILES.get('featured_image')
        if not featured_image:
            # Use default image if none provided
            from django.core.files.base import ContentFile
            import os
            default_image_path = os.path.join('media', 'blog/images/default.png')
            try:
                with open(default_image_path, 'rb') as f:
                    image_content = f.read()
                featured_image = ContentFile(image_content, name='default.png')
            except Exception as e:
                print(f"Default image not found at {default_image_path}: {e}")
                featured_image = None

        # Validate required fields
        missing_fields = []
        if not title:
            missing_fields.append('title')
        if not content:
            missing_fields.append('content')
        if not author_username:
            missing_fields.append('author_username')
        if missing_fields:
            return JsonResponse({'status': 'error', 'message': 'Missing required fields', 'missing_fields': missing_fields}, status=400)

        # Get author user
        try:
            author = User.objects.get(username=author_username)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Author user not found'}, status=404)

        # Create blog post
        blog = create_blog_post_bal(title, content, excerpt, category, tags, featured_image, author)
        if not blog:
            return JsonResponse({'status': 'error', 'message': 'Failed to create blog post'}, status=500)

        return JsonResponse({'status': 'success', 'slug': blog.slug, 'id': blog.id})
    except Exception as e:
        log_error_to_file(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def render_error_page(request, status=404):
    return render(request, 'pages/404.html', status=status)

def custom_404_view(request, exception):
    return render_error_page(request, status=404)

def custom_500_view(request):
    return render_error_page(request, status=500)

def error_page(request):
    return render_error_page(request, status=404)
