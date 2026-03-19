const { callService } = require('../../utils/api');

Page({
  data: { list: [] },
  onShow() {
    callService('getMyInstruments').then((res) => this.setData({ list: res.list }));
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  goPublish() {
    wx.navigateTo({ url: '/pages/instrument-publish/index' });
  },
  goEdit(event) {
    wx.navigateTo({ url: `/pages/instrument-edit/index?id=${event.currentTarget.dataset.id}` });
  }
});
