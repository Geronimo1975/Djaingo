from django.urls import path
from .views import views, authentication, tools, pages


urlpatterns = [
    path('', views.index, name='aiwave-index'),
    path('signup/', authentication.signup, name='aiwave-signup'),
    path('signin/', authentication.signin, name='aiwave-signin'),
    path('forgot-password/', authentication.forgotPassword, name='aiwave-forgot-password'),
    path('logout/', authentication.userLogout, name='aiwave-logout'),
    path('delete-user-profile/', authentication.deleteUserProfile, name='deleteUserProfile'),

    path('text-generator/', tools.textGenerator, name='aiwave-text-generator'),
    path('code-generator/', tools.codeGenerator, name='aiwave-code-generator'),
    path('email-generator/', tools.emailGenerator, name='aiwave-email-generator'),
    path('blog-generator/', tools.blogGenerator, name='aiwave-blog-generator'), 
    path('description-generator/', tools.descriptionGenerator, name='aiwave-description-generator'),
    path('summary-generator/', tools.summaryGenerator, name='aiwave-summary-generator'),
    path('get-sessions/', tools.getSessions, name='aiwave-get-sessions'),
    path('get-messages/', tools.getMessages, name='aiwave-get-messages'),
    path('delete-session/<uuid:session_id>/', tools.deleteSession, name='delete-session'),
    path('message-feedback/', tools.setFeedback, name='message-feedback'),
    path('blog/', pages.blog, name='aiwave-blog'),
    path('blog/create/', pages.createBlog, name='aiwave-blog-create'),
    path('blog/<slug:slug>/', pages.blogDetails, name='aiwave-blog-details'),
    path('blog/delete/<int:pk>/', pages.deleteBlog, name='aiwave-blog-delete'),
    path('pricing/', pages.pricing, name='aiwave-pricing'),
    path('contact/', pages.contact, name='aiwave-contact'),
    path('team/', pages.team, name='aiwave-team'),
    path('terms-policy/', pages.terms, name='aiwave-terms-policy'),
    path('privacy-policy/', pages.privacy, name='aiwave-privacy-policy'),

    path('profile-details/', pages.profile, name='aiwave-profile-details'),
    path('chat-export/', pages.chatExports, name='aiwave-chat-export'),
    path('api/export-chats/', pages.exportChatSessions, name='aiwave-export-chats'),
    path('plans-billing/', pages.plansBilling, name='aiwave-plans-billing'),
    path('release-notes/', pages.releaseNotes, name='aiwave-release-notes'),
    path('help/', pages.help, name='aiwave-help'),

    # Session Management URLs
    path('sessions/', pages.sessionsPage, name='aiwave-sessions-page'),
    path('api/sessions/', pages.getActiveSessions, name='aiwave-get-active-sessions'),
    path('api/sessions/terminate/', pages.terminateSession, name='aiwave-terminate-session'),
    path('api/sessions/terminate-all/', pages.terminateAllSessions, name='aiwave-terminate-all-sessions'),
    path('api/n8n-create-blog/', pages.n8n_create_blog, name='aiwave-n8n-create-blog'),
    path('404/', pages.error_page, name='aiwave-error-page'),
]