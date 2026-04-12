const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '操作失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    loading: true,
    list: [],
    total: 0,
    depositTotal: 0,
    insuranceTotal: 0,
    serviceTotal: 0
  },
  onShow() {
    this.loadData();
  },
  loadData() {
    callService('getCart')
      .then((res) => {
        this.setData({
          loading: false,
          list: res.list,
          total: res.total,
          depositTotal: res.depositTotal,
          insuranceTotal: res.insuranceTotal,
          serviceTotal: res.serviceTotal
        });
      })
      .catch(showError);
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  removeItem(event) {
    callService('removeCartItem', { id: event.currentTarget.dataset.id })
      .then(() => {
        wx.showToast({ title: '已移出购物车', icon: 'none' });
        this.loadData();
      })
      .catch(showError);
  },
  openInstrument(event) {
    wx.navigateTo({
      url: `/pages/equipment-detail/index?id=${event.currentTarget.dataset.id}`
    });
  },
  goConfirm(event) {
    const { instrumentId, tradeMode } = event.currentTarget.dataset;
    wx.navigateTo({
      url: `/pages/order-confirm/index?instrumentId=${instrumentId}&tradeMode=${encodeURIComponent(tradeMode)}`
    });
  }
});
