odoo.define("ws_pos_square_payment_terminal.payment", function (require) {
  "use strict";

  var core = require("web.core");
  var rpc = require("web.rpc");
  var terminal;
  var simulate_card_response;
  var PaymentInterface = require("point_of_sale.PaymentInterface");
  const { Gui } = require("point_of_sale.Gui");
  var ajax = require("web.ajax");
  var is_simulated_reader = "";
  var payment_id = null;
  var payment_method_id = null;
  var is_connected = false;
  var device_id = null;
   var _t = core._t;

  var SquarePaymentTerminal = PaymentInterface.extend({

    send_payment_request: function (cid) {
      this.was_cancelled = false;
      is_connected = false;
      self = this;
      payment_id = null
      device_id = null;
      var line = this.pos.get_order().selected_paymentline;
      payment_method_id = line.payment_method.id;
      this._super.apply(this, arguments);
     
      return rpc
        .query({
          model: "pos.payment.method",
          method: "check_device_status",
          args: [line.payment_method.id],
        }).then(function (result) {
          if (result.error) {

           
            simulate_card_response = false;
            self._show_error(
              _t(result.message)
            );
            line.set_payment_status("retry");
            return Promise.resolve();
          }
          else if(result.status=='UNPAIRED'){
           self._show_error(
              _t(result.message)
            );
            line.set_payment_status("retry");
          }
          else if(result.status=='EXPIRED'){
           self._show_error(
              _t(result.message)
            );
            line.set_payment_status("retry");
          }
           else if (result.status=='PAIRED') {
           device_id = result.device_id
            return self._ws_pos_square_payment_terminal_pay();
          }
          else{
           self._show_error(
              _t(result.message)
            );
            line.set_payment_status("retry");
          }
        });
    },

    _ws_pos_square_payment_terminal_pay: function () {
        var self = this;
        var line = this.pos.get_order().selected_paymentline;
        var order = this.pos.get_order();
        if (!line) {
            return Promise.reject();
        }
        if (this.was_cancelled) {
            return Promise.resolve();
        }
        // refund from square
        debugger;
        if (order.selected_paymentline.amount < 0 && line.order.selected_orderline.refunded_orderline_id) {
            return self._sd_square_payment_terminal_refund(line.order.selected_orderline,line).then(function(refund_res){
            if (!refund_res.error){
                order.selected_paymentline.refunded_id = refund_res.id
                return true
            }
            else{
              line.set_payment_status("retry");
              return false
            }

            });
        }
        else if (order.selected_paymentline.amount < 0) {
            this._show_error(
                _t("Cannot process transactions with negative amount.")
            );
            return Promise.resolve();
        }


      if (order === this.poll_error_order) {
        delete this.poll_error_order;
        return self._ws_pos_square_payment_terminal_handle_response({});
      }

        // line.set_payment_status("waiting");
        // return this.connection_square().then(function (data) {
        return self._ws_pos_square_payment_terminal_handle_response();
        // });
    },

    // square terminal refund
    _sd_square_payment_terminal_refund: function(data,line){
        // refund from Square payment terminal
         var currency = this.pos.currency.name;
         return  rpc.query({
          model: "pos.payment.method",
          method: "square_refund_payment",
          args: [payment_method_id,data.refunded_orderline_id,parseInt(line.amount*(100)) ,currency],
        }).then(function (response) {
          return response;
        }).then(function(response) {
            if (response.error == false){
                console.log('refunded data : ',response.message)
                Promise.resolve();
                return response
            }
            else{
                 self._show_error(_t(response.message));
                 line.set_payment_status("retry");
                 Promise.reject()
                 return response
            }

        });

        },

    _ws_pos_square_payment_terminal_handle_response: function () {
      if (this.was_cancelled) {
        return Promise.resolve();
      }
      var line = this.pos.get_order().selected_paymentline;

        var self = this;

        var res = new Promise(function (resolve, reject) {
          // clear previous intervals just in case, otherwise
          // it'll run forever

          clearTimeout(self.polling);

          var is_test = false;
          var location_id;
          var device_name;
          var registration_code;
          if (line.payment_method.account_type=="sandbox") {
            is_test = true;
          } else {
            location_id = line.payment_method.location_id;
            device_name = line.payment_method.device_name;
            registration_code = line.payment_method.token_key;
          }

          var square_payment_request = self.squarePaymentRequest();

          square_payment_request.then(function (resp) {
         
            console.log("response for payment request......", resp);
            if (self.was_cancelled) {
              resolve(false);
              return Promise.resolve();
              clearTimeout(self.polling);
            }
             if (resp && !resp.error) {
                console.log('Payment request Status: ',resp.status)
               var time_out = setTimeout(function () {
                line.set_payment_status("waitingCard");
                    self.polling = setInterval(function () {

                      var test = self._square_poll_for_response(resolve, reject, resp.checkout_id);
                      if (self.last_diagnosis_service_id == true) {
                        clearTimeout(this.polling);
                      }
//                      clearInterval(self.polling);
                      return test;

                }, 8500);

          }, 10000);

             if (self.last_diagnosis_service_id == true) {
                        clearTimeout(time_out);
                      }
             }
                else {
                  line.set_payment_status("retry");

                  var message;
                  if (resp && resp.message) {
                  message = resp.message

                  } else {
                    message = "Failed to connect to the reader. Please retry again!";
                  }

                  console.log("Message", message);
                  self._show_error(_t(message));

                  resolve(false);
                }
          });
        });

        // make sure to stop polling when we're done
        res.finally(function () {
          self._reset_state();
        });

        return res;

    },

     // private methods
     _reset_state: function() {
        this.was_cancelled = false;
        this.last_diagnosis_service_id = false;
        this.remaining_polls = 4;
        clearTimeout(this.polling);
     },

    _square_poll_for_response: function (resolve, reject, checkout_id) {
      var line = this.pos.get_order().selected_paymentline;
      if (!line) {
        return Promise.reject();
      }

      var self = this;
      if (this.was_cancelled) {
        resolve(false);
        return Promise.resolve();
      }
       var payment_status = self._check_payment_status(checkout_id);

        return payment_status.then(function (data) {
          //            if there is error in response
          if (data){
             if (data.error) {
                if (self.remaining_polls != 0) {
                  self.remaining_polls--;
                  return Promise.reject();
                   self._show_error(
                  _t(data.message)
                );
                } else {
                  reject();
                  self.poll_error_order = self.pos.get_order();
                  return Promise.reject();
                   self._show_error(
                  _t(data.message))
                }
                resolve(false);
                return Promise.reject();
              }
              else {
                is_connected = true;
                var clientSecret = data;
                if (data.status=='COMPLETED'){
                    line.transaction_id = data.checkout_id;
                    line.payment_ref = data.payment_ref;
                    line.set_payment_status("done");
                    resolve(true);
                    self.last_diagnosis_service_id = true;
                }
                if (data.status=='IN_PROGRESS'){
                    line.transaction_id = payment_id;
                }
                if (data.status=='CANCELED'){
                    self._show_error(
                      _t('Cancelled: Payment transaction has been cancelled!'))
                       line.set_payment_status("retry");
                       resolve(false);
                }
                if (data.status=='FAILED'){
                    self._show_error(
                      _t('Payment transaction has been Failed,PLease check the status of Payment on square account.',))
                       self._ws_pos_square_payment_terminal_cancel();
                       line.set_payment_status("retry");
                       resolve(false);
                }
              }
          }



          if (self.remaining_polls <= 0) {
            self._show_error(
              _t(
                "The connection to your payment terminal failed. Please check if it is still connected to the internet."
              )
            );
            self._ws_pos_square_payment_terminal_cancel();
            resolve(false);
          }
        });

    },

    _ws_pos_square_payment_terminal_cancel: function () {
      var self = this;
      var data = "";
      var line = this.pos.get_order().selected_paymentline;

     
      if (payment_id) {

          return rpc.query({
              model: "pos.payment.method",
              method: "cancel_payment",
              args: [payment_method_id,payment_id],
            }).then(function (response) {
              return response;
            }).then(function (data) {
            if (data){
            if (data.error) {

                console.log("Sorry! could not cancelled payment. " + data.message);


              }
              else {

                 console.log("Successfully Cancelled the payment");


                return data;
              }
            }

            });

      }
    },

    squarePaymentRequest: function () {
      var line = this.pos.get_order().selected_paymentline;
      var line_amount = line.amount;
      var currency = this.pos.currency.name;
      var real_amount = parseInt(line_amount * (100));
      console.log('real_amount********',real_amount)


      console.log("calling payment request...");
      return rpc.query({
          model: "pos.payment.method",
          method: "request_for_payment",
          args: [payment_method_id,real_amount,currency,device_id],
        }).then(function (response) {
          return response;
        })
        .then(function (data) {
          if (data.error) {
            self._show_error(
              _t(data.message)
            );
            console.log("Sorry! Could not process the Payment. " + data.message);
            var line = self.pos.get_order().selected_paymentline;
            line.set_payment_status("retry");
            return Promise.reject();
            //              return data;
          } else {
            payment_id = data.checkout_id
            return data;
          }
        });
    },

    _check_payment_status: function(checkout_id){
        return rpc.query({
              model: "pos.payment.method",
              method: "check_payment_status",
              args: [payment_method_id,checkout_id],
            }).then(function (data) {
            console.log('***************data******',data)
              if (data && data.error) {
                self._show_error(
                  _t(data.message)
                );
                console.log("Sorry! Could not process the Payment. " + data.error);
                var line = self.pos.get_order().selected_paymentline;
                line.set_payment_status("retry");
                return Promise.reject();
                //              return data;
              } else if (data) {


                return data;
              }
            });
    },

    send_payment_cancel: function (order, cid) {
    
      clearInterval(this.polling);
      this._super.apply(this, arguments);
      this.was_cancelled = true;
      if (payment_id) {
        this._ws_pos_square_payment_terminal_cancel();
      }

      return Promise.resolve();
    },

    _show_error: function (msg, title) {
      clearInterval(this.polling);
      this.was_cancelled = true;
      if (!title) {
        title = _t("Square Terminal Error:");
      }
      Gui.showPopup("ErrorPopup", {
        title: title,
        body: msg,
      });
//      return Promise.reject();
    },

  });
  return SquarePaymentTerminal;

});
