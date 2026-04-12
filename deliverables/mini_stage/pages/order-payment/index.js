const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '加载失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    order: null,
    instrument: null
  },
  onLoad(options) {
    const orderId = options.orderId;
    Promise.all([
      callService('getPaymentInfo', { orderId }),
      callService('getOrderDetail', { id: orderId })
    ])
      .then(([paymentInfo, detail]) => {
        this.setData({
          order: paymentInfo.order,
          instrument: detail.instrument
        });
      })
      .catch(showError);
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  goAgreement() {
    const instrumentId = this.data.instrument && this.data.instrument.id;
    wx.navigateTo({
      url: instrumentId ? `/pages/agreement/index?instrumentId=${instrumentId}` : '/pages/agreement/index'
    });
  },
  payNow() {
    callService('confirmPayment', { orderId: this.data.order.id })
      .then((res) => {
        wx.navigateTo({
          url: `/pages/order-success/index?orderId=${res.orderId}`
        });
      })
      .catch(showError);
  }
});
