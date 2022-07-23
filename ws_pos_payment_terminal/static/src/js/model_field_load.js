odoo.define('ws_pos_payment_terminal.model_field_load', function (require) {
    const models = require('point_of_sale.models');
    const _super_Paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function(attributes,options){
         _super_Paymentline.initialize.apply(this,arguments);
            var self = this;
            this.refunded_id = "";
            this.payment_ref = "";
        },
         export_as_JSON: function () {
            return _.extend(_super_Paymentline.export_as_JSON.apply(this,
            arguments), {
                refunded_id : this.refunded_id,
                payment_ref : this.payment_ref,
                });
        },

        init_from_JSON: function(json_value){
            _super_Paymentline.init_from_JSON.apply(this, arguments);
            this.refunded_id = json_value.refunded_id ;
            this.payment_ref = json_value.refunded_id ;
        },

    });

});
