import json
import logging
import re
import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

KLAVIYO_API_URL = "https://a.klaviyo.com/api/events/"


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    klaviyo_resolution_type = fields.Selection([
        ('complaint_resolved', 'Complaint Resolved'),
        ('delivery_delay_confirmed', 'Delivery Delay Confirmed'),
        ('goodwill_approved', 'Goodwill Approved'),
    ], string='Resolution Type', tracking=True,
       help='Select the resolution type to trigger the appropriate Klaviyo event')
    
    klaviyo_event_sent = fields.Boolean(
        string='Klaviyo Event Sent',
        default=False,
        copy=False,
        help='Indicates if the Klaviyo event has been sent for this ticket'
    )
    
    klaviyo_event_log_ids = fields.One2many(
        'klaviyo.event.log',
        'ticket_id',
        string='Klaviyo Event Logs'
    )
    
    klaviyo_goodwill_amount = fields.Float(
        string='Goodwill Amount',
        help='Amount offered as goodwill gesture (for goodwill_approved events)'
    )
    
    klaviyo_coupon_code = fields.Char(
        string='Coupon Code',
        help='Coupon code to include in the event (if applicable)'
    )

    def action_send_klaviyo_event(self):
        """Manually send Klaviyo event for this ticket"""
        self.ensure_one()
        
        if not self.klaviyo_resolution_type:
            raise UserError(_('Please select a Resolution Type before sending the Klaviyo event.'))
        
        if not self.partner_id or not self.partner_id.email:
            raise UserError(_('Customer email is required to send Klaviyo event.'))
        
        self._send_klaviyo_event()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Klaviyo event sent successfully!'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_resolve_and_send_klaviyo(self):
        """Resolve ticket and send Klaviyo event"""
        self.ensure_one()
        
        if not self.klaviyo_resolution_type:
            raise UserError(_('Please select a Resolution Type before resolving the ticket.'))
        
        # Send Klaviyo event
        self._send_klaviyo_event()
        
        # Mark ticket as resolved - find the closing stage
        stage_model = self.env['helpdesk.stage']
        # Determine correct field name for "closed" stage (varies by Odoo version)
        close_field = (
            'is_close' if 'is_close' in stage_model._fields
            else 'closed' if 'closed' in stage_model._fields
            else 'fold' if 'fold' in stage_model._fields
            else None
        )
        if close_field:
            resolved_stage = stage_model.search([
                (close_field, '=', True),
                '|',
                ('team_ids', 'in', self.team_id.ids),
                ('team_ids', '=', False)
            ], limit=1)
            if resolved_stage:
                self.stage_id = resolved_stage
        
        return True

    def _send_klaviyo_event(self):
        """Send event to Klaviyo API"""
        self.ensure_one()
        
        if self.klaviyo_event_sent:
            _logger.info('Klaviyo event already sent for ticket %s. Skipping.', self.name)
            return False
        
        # Check if Klaviyo is enabled
        klaviyo_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'klaviyo_integration.enabled', 'False'
        )
        if klaviyo_enabled.lower() != 'true':
            _logger.info('Klaviyo integration is disabled. Skipping event.')
            return False
        
        # Get API key
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'klaviyo_integration.api_key', ''
        )
        if not api_key:
            raise UserError(_('Klaviyo API Key is not configured. Please configure it in Settings.'))
        
        # Get API revision
        api_revision = self.env['ir.config_parameter'].sudo().get_param(
            'klaviyo_integration.api_revision', '2024-02-15'
        )
        
        # Build event payload
        event_name = self._get_klaviyo_event_name()
        payload = self._build_klaviyo_payload(event_name)
        
        # Create log entry
        log = self.env['klaviyo.event.log'].create({
            'name': event_name,
            'ticket_id': self.id,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'email': self.partner_id.email if self.partner_id else '',
            'event_type': self.klaviyo_resolution_type,
            'payload': json.dumps(payload, indent=2),
            'state': 'pending',
        })
        
        # Send to Klaviyo
        headers = {
            'Authorization': f'Klaviyo-API-Key {api_key}',
            'Content-Type': 'application/json',
            'revision': api_revision,
        }
        
        try:
            response = requests.post(
                KLAVIYO_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            log.write({
                'response_code': response.status_code,
                'response_body': response.text[:2000] if response.text else '',
            })
            
            if response.status_code in [200, 201, 202]:
                log.write({'state': 'success'})
                self.klaviyo_event_sent = True
                _logger.info(f'Klaviyo event sent successfully for ticket {self.name}')
            else:
                log.write({
                    'state': 'failed',
                    'error_message': f'API returned status code {response.status_code}: {response.text[:500]}'
                })
                _logger.error(f'Klaviyo API error for ticket {self.name}: {response.status_code} - {response.text}')
                
        except requests.exceptions.Timeout:
            log.write({
                'state': 'failed',
                'error_message': 'Request timeout - Klaviyo API did not respond in time'
            })
            _logger.error(f'Klaviyo API timeout for ticket {self.name}')
            
        except requests.exceptions.RequestException as e:
            log.write({
                'state': 'failed',
                'error_message': str(e)
            })
            _logger.error(f'Klaviyo API request error for ticket {self.name}: {str(e)}')
        
        return log.state == 'success'

    def _get_klaviyo_event_name(self):
        """Get the Klaviyo event name based on resolution type"""
        event_names = {
            'complaint_resolved': 'Complaint Resolved',
            'delivery_delay_confirmed': 'Delivery Delay Confirmed',
            'goodwill_approved': 'Goodwill Approved',
        }
        return event_names.get(self.klaviyo_resolution_type, 'Ticket Resolved')

    def _build_klaviyo_payload(self, event_name):
        """Build the Klaviyo event payload"""
        # Get related sale order if exists
        sale_order = self._get_related_sale_order()
        
        # Build properties
        properties = {
            'ticket_id': self.id,
            'ticket_name': self.name,
            'ticket_number': self.ticket_ref if hasattr(self, 'ticket_ref') else self.name,
            'resolution_type': self.klaviyo_resolution_type,
            'resolution_date': fields.Datetime.now().isoformat(),
        }
        
        # Add ticket description if available (strip HTML tags)
        if self.description:
            clean_desc = re.sub(r'<[^>]+>', ' ', self.description)
            clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
            properties['ticket_description'] = clean_desc[:500]
        
        # Add goodwill amount if applicable
        if self.klaviyo_resolution_type == 'goodwill_approved' and self.klaviyo_goodwill_amount:
            properties['goodwill_amount'] = self.klaviyo_goodwill_amount
        
        # Add coupon code if available
        if self.klaviyo_coupon_code:
            properties['coupon_code'] = self.klaviyo_coupon_code
        
        # Add sale order info if available
        if sale_order:
            properties.update({
                'order_id': sale_order.id,
                'order_name': sale_order.name,
                'order_total': sale_order.amount_total,
                'order_date': sale_order.date_order.isoformat() if sale_order.date_order else '',
            })
        
        # Build the full payload
        payload = {
            'data': {
                'type': 'event',
                'attributes': {
                    'metric': {
                        'data': {
                            'type': 'metric',
                            'attributes': {
                                'name': event_name
                            }
                        }
                    },
                    'profile': {
                        'data': {
                            'type': 'profile',
                            'attributes': {
                                'email': self.partner_id.email,
                                'first_name': self.partner_id.name.split()[0] if self.partner_id.name else '',
                                'last_name': ' '.join(self.partner_id.name.split()[1:]) if self.partner_id.name and len(self.partner_id.name.split()) > 1 else '',
                            }
                        }
                    },
                    'properties': properties,
                    'time': fields.Datetime.now().isoformat() + 'Z',
                }
            }
        }
        
        # Add phone if available
        if self.partner_id.phone:
            payload['data']['attributes']['profile']['data']['attributes']['phone_number'] = self.partner_id.phone
        
        return payload

    def _get_related_sale_order(self):
        """Get related sale order if exists"""
        # Try to find sale order from ticket
        if hasattr(self, 'sale_order_id') and self.sale_order_id:
            return self.sale_order_id
        
        # Try to find from source document
        if hasattr(self, 'source_document') and self.source_document:
            sale_order = self.env['sale.order'].search([
                ('name', '=', self.source_document)
            ], limit=1)
            if sale_order:
                return sale_order
        
        return False

    @api.model
    def _cron_retry_failed_klaviyo_events(self):
        """Cron job to retry failed Klaviyo events"""
        failed_logs = self.env['klaviyo.event.log'].search([
            ('state', '=', 'failed'),
            ('create_date', '>=', fields.Datetime.subtract(fields.Datetime.now(), days=7))
        ], limit=50)
        
        for log in failed_logs:
            if log.ticket_id and not log.ticket_id.klaviyo_event_sent:
                try:
                    log.ticket_id._send_klaviyo_event()
                except Exception as e:
                    _logger.error(f'Failed to retry Klaviyo event for ticket {log.ticket_id.name}: {str(e)}')
