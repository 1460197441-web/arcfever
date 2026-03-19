const { callService } = require('../../utils/api');

Page({
  data: {
    loading: true,
    profile: null
  },
  onLoad() {
    callService('getProfile').then((profile) => {
      this.setData({ loading: false, profile });
    });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  goPage(event) {
    wx.navigateTo({ url: event.currentTarget.dataset.page });
  }
});
