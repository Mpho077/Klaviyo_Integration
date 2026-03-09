from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    klaviyo_api_key = fields.Char(
        string='Klaviyo API Key',
        config_parameter='klaviyo_integration.api_key',
        help='Enter your Klaviyo Private API Key'
    )
    klaviyo_enabled = fields.Boolean(
        string='Enable Klaviyo Integration',
        config_parameter='klaviyo_integration.enabled',
        default=False,
        help='Enable or disable Klaviyo event sending'
    )
    klaviyo_api_revision = fields.Char(
        string='Klaviyo API Revision',
        config_parameter='klaviyo_integration.api_revision',
        default='2024-02-15',
        help='Klaviyo API revision date (format: YYYY-MM-DD)'
    )
