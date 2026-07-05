from wowdash_app.models import ContentSetting
from django.conf import settings
import logging
from Dal.wowdash_app.siteMetaSettings import get_all_site_settings

logger = logging.getLogger(__name__)

def site_image(request):
    chat_bot_img = ContentSetting.objects.filter(key="chat_bot_image").first()
    
    return {
        'bot_image': chat_bot_img
    }

# New context processor for site meta settings

def site_meta_vars(request):
    """
    Provides meta_vars for site meta settings pages (contact info, file upload, general site, social media, access/security)
    Uses existing DAL function for efficiency
    """
    try:
        # Use existing DAL function to get all settings
        all_settings = get_all_site_settings()
        
        # Define the keys we want to expose
        keys = [
            'company_address', 'contact_email', 'contact_phone',
            'allowed_file_types', 'max_file_size',
            'site_name', 'site_description', 'site_logo', 'favicon_png', 'small_logo',
            'social_facebook', 'social_linkedin', 'social_twitter',
        ]
        
        # Create settings dict with defaults
        settings_dict = {k: all_settings.get(k, None) for k in keys}
        
        # Map the database keys to template-friendly names
        settings_dict['site_img'] = settings_dict.get('site_logo', '')
        settings_dict['favicon_logo'] = settings_dict.get('favicon_png', '')
        settings_dict['small_logo'] = settings_dict.get('small_logo', '')
        
        return {'meta_vars': settings_dict}
        
    except Exception as e:
        logger.error(f"Error in site_meta_vars context processor: {e}")
        # Return empty dict on error to prevent template errors
        return {'meta_vars': {}}