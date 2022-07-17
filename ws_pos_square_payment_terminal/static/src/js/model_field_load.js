odoo.define('ws_pos_square_payment_terminal.model_field_load', function (require) {
const models = require('point_of_sale.models');
const _super_Paymentline = models.Paymentline.prototype;



  models.Paymentline = models.Paymentline.extend({
        initialize: function(attributes,options){
         _super_Paymentline.initialize.apply(this,arguments);
            var self = this;
            this.refunded_id = "";


        },
         export_as_JSON: function () {
        return _.extend(_super_Paymentline.export_as_JSON.apply(this, arguments), {

                                                                                refunded_id : this.refunded_id,

                                                                                });
    },

        init_from_JSON: function(json_value){

             _super_Paymentline.init_from_JSON.apply(this, arguments);
             debugger

            this.refunded_id = json_value.refunded_id ;
        },

    });

});
