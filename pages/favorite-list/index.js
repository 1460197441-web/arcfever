const { callService } = require('../../utils/api');

Page({
  data: { list: [] },
  onLoad() {
    callService('getFavoriteList').then((res) => this.setData({ list: res.list }));
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  openInstrument(event) {
    wx.navigateTo({ url: `/pages/equipment-detail/index?id=${event.currentTarget.dataset.id}` });
  }
});
