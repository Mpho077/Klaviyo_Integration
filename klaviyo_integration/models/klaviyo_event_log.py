from odoo import api, fields, models


class KlaviyoEventLog(models.Model):
    _name = 'klaviyo.event.log'
    _description = 'Klaviyo Event Log'
    _order = 'create_date desc'

    name = fields.Char(string='Event Name', required=True)
    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket', ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Customer')
    email = fields.Char(string='Customer Email')
    event_type = fields.Selection([
        ('complaint_resolved', 'Complaint Resolved'),
        ('delivery_delay_confirmed', 'Delivery Delay Confirmed'),
        ('goodwill_approved', 'Goodwill Approved'),
    ], string='Event Type', required=True)
    payload = fields.Text(string='Payload Sent')
    response_code = fields.Integer(string='Response Code')
    response_body = fields.Text(string='Response Body')
    state = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ], string='Status', default='pending')
    error_message = fields.Text(string='Error Message')
