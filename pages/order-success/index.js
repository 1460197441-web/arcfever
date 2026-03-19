Page({
  data: {
    orderId: ''
  },
  onLoad(options) {
    this.setData({ orderId: options.orderId || '' });
  },
  goOrderList() {
    wx.navigateTo({ url: '/pages/order-list/index' });
  },
  goHome() {
    wx.reLaunch({ url: '/pages/home/index' });
  }
});
