from odoo import api, fields, models


class HelpdeskTicketReport(models.Model):
    _inherit = 'helpdesk.ticket.report.analysis'

    klaviyo_resolution_type = fields.Selection([
        ('complaint_resolved', 'Complaint Resolved'),
        ('delivery_delay_confirmed', 'Delivery Delay Confirmed'),
        ('goodwill_approved', 'Goodwill Approved'),
    ], string='Resolution Type', readonly=True)

    klaviyo_goodwill_amount = fields.Float(
        string='Goodwill Amount', readonly=True)

    klaviyo_event_sent = fields.Boolean(
        string='Klaviyo Event Sent', readonly=True)

    @api.model
    def _select(self):
        return super()._select() + """,
            T.klaviyo_resolution_type,
            T.klaviyo_goodwill_amount,
            T.klaviyo_event_sent"""

    @api.model
    def _group_by(self):
        return super()._group_by() + """,
            T.klaviyo_resolution_type,
            T.klaviyo_goodwill_amount,
            T.klaviyo_event_sent"""
