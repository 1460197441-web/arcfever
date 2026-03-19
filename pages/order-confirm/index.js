const { callService } = require('../../utils/api');

Page({
  data: {
    preview: null,
    remark: ''
  },
  onLoad() {
    callService('getOrderPreview').then((preview) => {
      this.setData({ preview });
    });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    this.setData({ remark: event.detail.value });
  },
  submitOrder() {
    callService('createOrder', { remark: this.data.remark }).then((res) => {
      wx.navigateTo({
        url: `/pages/order-payment/index?orderId=${res.orderId}`
      });
    });
  }
});
