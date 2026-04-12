const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '订单加载失败',
    icon: 'none'
  });
}

Page({
  data: { list: [] },
  onShow() {
    callService('getOrderList')
      .then((res) => this.setData({ list: res.list }))
      .catch(showError);
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  openOrder(event) {
    wx.navigateTo({ url: `/pages/order-detail/index?id=${event.currentTarget.dataset.id}` });
  }
});
