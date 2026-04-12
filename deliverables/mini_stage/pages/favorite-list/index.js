const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '收藏加载失败',
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
    callService('getFavoriteList')
      .then((res) => this.setData({ list: res.list, loading: false }))
      .catch((error) => {
        this.setData({ loading: false });
        showError(error);
      });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  openInstrument(event) {
    wx.navigateTo({ url: `/pages/equipment-detail/index?id=${event.currentTarget.dataset.id}` });
  }
});
