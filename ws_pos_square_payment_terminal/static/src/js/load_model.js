odoo.define('ws_pos_square_payment_terminal.models', function (require) {
var models = require('point_of_sale.models');
var PosSquarePaymentTerminal = require('ws_pos_square_payment_terminal.payment');

models.register_payment_method('ws_pos_square_payment_terminal', PosSquarePaymentTerminal);
models.load_fields('pos.payment.method', ['application_id','token_key','location_id','device_name','web_hook_url','device_code']);
});