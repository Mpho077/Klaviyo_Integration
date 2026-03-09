{
    'name': 'Klaviyo Integration',
    'version': '19.0.1.0.0',
    'category': 'Marketing',
    'summary': 'Send ticket resolution events to Klaviyo',
    'description': """
        Klaviyo Integration for Helpdesk Tickets
        =========================================
        
        This module sends events to Klaviyo when helpdesk tickets are resolved.
        
        Features:
        - Sends events to Klaviyo API on ticket resolution
        - Supports multiple event types:
            * complaint_resolved
            * delivery_delay_confirmed
            * goodwill_approved
        - Configurable API key in settings
        - Logs all API calls for debugging
        
        Coupons are generated in Shopify via Klaviyo flows.
    """,
    'author': 'Bathroom Sales Direct',
    'website': 'https://www.bathroomsalesdirect.com.au',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'helpdesk',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/helpdesk_ticket_views.xml',
        'data/klaviyo_event_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
