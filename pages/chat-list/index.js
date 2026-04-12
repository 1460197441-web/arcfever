const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '消息列表加载失败',
    icon: 'none'
  });
}

Page({
  data: {
    loading: true,
    list: []
  },
  onShow() {
    this.syncTabBar();
    this.loadData();
  },
  loadData() {
    this.setData({ loading: true });
    callService('getChatList')
      .then((res) => this.setData({ list: res.list || [], loading: false }))
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
  openChat(event) {
    wx.navigateTo({ url: `/pages/chat-detail/index?id=${event.currentTarget.dataset.id}` });
  }
});
