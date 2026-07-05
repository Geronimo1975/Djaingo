from django.urls import path
from .views import wowdash, user, environmentSettings, dashboard, siteMetaSettings

urlpatterns = [

    path('', dashboard.index, name='wowdash-index'),
    path('api/users/<int:user_id>/toggle-status/', dashboard.toggleUserStatus, name='toggleUserStatus'),
    path('api/dashboard/stats/', dashboard.getStats, name='dashboard_stats'),

    # Wowdash URLs
    path('team/', wowdash.team, name='team'),
    path('team/add/', wowdash.add_team_member, name='add_team_member'),
    path('team/<int:member_id>/edit/', wowdash.edit_team_member, name='edit_team_member'),
    path('team/<int:member_id>/delete/', wowdash.delete_team_member, name='delete_team_member'),
    path('team/<int:member_id>/toggle-featured/', wowdash.edit_team_member, name='toggle_team_member_featured'),
    path('pricing/', wowdash.pricing, name='pricing'),
    path('terms-condition/', wowdash.termsCondition, name='termsCondition'),
    path('privacy-policy/', wowdash.privacyPolicy, name='privacyPolicy'),
    path('release-notes/', wowdash.releaseNotes, name='releaseNotes'),
    path('release-note/delete/<int:pk>/', wowdash.releaseNoteDelete, name='releaseNoteDelete'),
    path('faq/', wowdash.faq, name='faq'),
    path('faqs/create/', wowdash.faqCreate, name='faq_create'),
    path('faqs/<int:faq_id>/edit/', wowdash.faqEdit, name='faq_edit'),
    path('faqs/<int:faq_id>/delete/', wowdash.faqDelete, name='faq_delete'),
    path('faqs/<int:faq_id>/toggle-visibility/', wowdash.faqToggleVisibility, name='faq_toggle_visibility'),
    path('user-inquiries/', wowdash.userInquiries, name='userInquiries'),
    path('delete-query/<int:query_id>/', wowdash.deleteQuery, name='delete_query'),
    path('user-inquiries/delete-all-read/', wowdash.deleteAllReadInquiries, name='deleteAllReadInquiries'),
    path('toggle-query-read/<int:query_id>/', wowdash.toggleQueryRead, name='toggle_query_read'),

    # Environment Settings URLs
    path('settings/', environmentSettings.settings, name='settings'),
    path('facebook-key-settings/', environmentSettings.facebookKey, name='facebookKeySettings'),
    path('gemini-key-settings/', environmentSettings.geminiKey, name='geminiKeySettings'),


    # Authentication URLs
    path('logout/', user.userLogout, name='logout'),


    # User URLs
    path('add-user/', user.addUser, name='addUser'),
    path('users-list/', user.usersList, name='usersList'),
    path('view-profile/', user.viewProfile, name='viewProfile'),
    path('api/users/', user.getUserData, name='getUsersData'),
    path('api/users/<int:user_id>/delete/', user.deleteUser, name='deleteUser'),
    path('api/profile/delete/', user.deleteUser, name='deleteProfile'),
    path('change-password/', user.changePassword, name='changePassword'),


    # Blog Management URLs
    path('blog/', wowdash.blogManagement, name='blogManagement'),
    path('blog/edit/<int:post_id>/', wowdash.editBlog, name='blogEdit'),
    path('blog/delete/<int:post_id>/', wowdash.blogDelete, name='blogDelete'),
    path('blog/preview/<int:post_id>/', wowdash.blogPreview, name='blogPreview'),

    path('settings/general/', siteMetaSettings.generalSettings, name='generalSiteSettings'),
    path('settings/contact/', siteMetaSettings.contactInformationSettings, name='contactInformationSettings'),
]
