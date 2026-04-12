const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '加载失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    loading: true,
    profile: null
  },
  onShow() {
    this.syncTabBar();
    callService('getProfile')
      .then((profile) => {
        this.setData({ loading: false, profile });
      })
      .catch((error) => {
        this.setData({ loading: false });
        showError(error);
      });
  },
  syncTabBar() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().syncSelected();
    }
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  goPage(event) {
    wx.navigateTo({ url: event.currentTarget.dataset.page });
  }
});
