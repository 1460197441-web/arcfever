const { callService } = require('../../utils/api');

Page({
  data: {
    loading: true,
    homeData: null
  },
  onLoad() {
    this.loadData();
  },
  loadData() {
    callService('getHomeData').then((homeData) => {
      this.setData({ homeData, loading: false });
    });
  },
  goPage(event) {
    wx.navigateTo({ url: event.currentTarget.dataset.page });
  },
  openInstrument(event) {
    wx.navigateTo({
      url: `/pages/equipment-detail/index?id=${event.currentTarget.dataset.id}`
    });
  }
});
