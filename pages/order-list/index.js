const { callService } = require('../../utils/api');

Page({
  data: { list: [] },
  onLoad() {
    callService('getOrderList').then((res) => this.setData({ list: res.list }));
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  openOrder(event) {
    wx.navigateTo({ url: `/pages/order-detail/index?id=${event.currentTarget.dataset.id}` });
  }
});
