const { callService } = require('../../utils/api');

Page({
  data: { list: [] },
  onLoad() {
    callService('getRatingList').then((res) => this.setData({ list: res.list }));
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  goPublish() {
    wx.navigateTo({ url: '/pages/rating-publish/index' });
  }
});
