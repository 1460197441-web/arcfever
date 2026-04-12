const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '我的仪器加载失败',
    icon: 'none'
  });
}

Page({
  data: { list: [] },
  onShow() {
    callService('getMyInstruments')
      .then((res) => this.setData({ list: res.list }))
      .catch(showError);
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  goPublish() {
    wx.switchTab({ url: '/pages/instrument-publish/index' });
  },
  goEdit(event) {
    wx.navigateTo({ url: `/pages/instrument-edit/index?id=${event.currentTarget.dataset.id}` });
  }
});
