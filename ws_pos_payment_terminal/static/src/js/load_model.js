odoo.define('ws_pos_payment_terminal.models', function (require) {
var models = require('point_of_sale.models');

models.load_fields('pos.payment.method', ['pos_name']);
});
