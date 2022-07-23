# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    pos_name = fields.Char('Name for POS', help="Fill in this field If you want to show different name on payment Screen")


class PosPayment(models.Model):
    _inherit = "pos.payment"

    payment_ref = fields.Char(string="Receipt Number", copy=False)
    refunded_id = fields.Char(string="Refunded ID", copy=False)

