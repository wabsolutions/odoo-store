# coding: utf-8
import logging
from odoo import fields, models, api, _
_logger = logging.getLogger(__name__)


class DeviceCode(models.Model):
    _name = 'device.code'
    _description = 'Square Device Code'

    name = fields.Char()
    device_code = fields.Char(string="Device Code")
    device_id = fields.Char(string="Device ID")
    code_id = fields.Char(string="Code ID")
    location_id = fields.Char(string="Location ID")
    product_type = fields.Char(string="Product Type")
    paired_at = fields.Datetime(string="Paired At")
    status = fields.Selection([
        ('paired', 'PAIRED'),
        ('expired', 'EXPIRED'),
        ('unpaired', 'UNPAIRED')], string="Status", default="unpaired", readonly=True, tracking=True)
    status_change_date = fields.Datetime(string="Status Changed On")


