const { callService } = require('../../utils/api');

Page({
  data: {
    loading: true,
    instrument: null,
    isFavorite: false,
    recommendations: []
  },
  onLoad(options) {
    callService('getInstrumentDetail', { id: options.id }).then((res) => {
      this.setData({
        loading: false,
        instrument: res.instrument,
        isFavorite: res.isFavorite,
        recommendations: res.recommendations
      });
    });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  addToCart() {
    callService('addToCart', { instrumentId: this.data.instrument.id }).then((res) => {
      wx.showToast({ title: res.message, icon: 'success' });
    });
  },
  goChat() {
    wx.navigateTo({ url: '/pages/chat-list/index' });
  },
  openInstrument(event) {
    wx.redirectTo({
      url: `/pages/equipment-detail/index?id=${event.currentTarget.dataset.id}`
    });
  }
});
