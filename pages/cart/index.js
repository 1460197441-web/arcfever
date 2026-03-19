const { callService } = require('../../utils/api');

Page({
  data: {
    loading: true,
    list: [],
    total: 0
  },
  onLoad() {
    callService('getCart').then((res) => {
      this.setData({ loading: false, list: res.list, total: res.total });
    });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  goConfirm() {
    wx.navigateTo({ url: '/pages/order-confirm/index' });
  }
});
