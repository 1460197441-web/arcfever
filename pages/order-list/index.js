const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '订单加载失败',
    icon: 'none'
  });
}

Page({
  data: {
    loading: true,
    list: []
  },
  onShow() {
    this.loadData();
  },
  loadData() {
    this.setData({ loading: true });
    callService('getOrderList')
      .then((res) => this.setData({ list: res.list || [], loading: false }))
      .catch((error) => {
        this.setData({ loading: false });
        showError(error);
      });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  goEquipment() {
    wx.navigateTo({ url: '/pages/equipment/index' });
  },
  goRemoteLab() {
    wx.navigateTo({ url: '/pages/remote-lab/index' });
  },
  openOrder(event) {
    wx.navigateTo({ url: `/pages/order-detail/index?id=${event.currentTarget.dataset.id}` });
  }
});
