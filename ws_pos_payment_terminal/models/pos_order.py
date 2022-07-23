# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosOrder(models.Model):
    """Inherit to Populate the custom field values from JS"""
    _inherit = "pos.order"

    def _payment_fields(self, order, ui_paymentline):
        rec = super(PosOrder, self)._payment_fields( order, ui_paymentline)
        rec['refunded_id'] = ui_paymentline.get('refunded_id', False)
        rec['payment_ref'] = ui_paymentline.get('payment_ref', False)
        return rec
