const { callService } = require('../../utils/api');

Page({
  data: {
    order: null
  },
  onLoad(options) {
    callService('getPaymentInfo', { orderId: options.orderId }).then((res) => {
      this.setData({ order: res.order });
    });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  payNow() {
    callService('confirmPayment', { orderId: this.data.order.id }).then((res) => {
      wx.navigateTo({
        url: `/pages/order-success/index?orderId=${res.orderId}`
      });
    });
  }
});
