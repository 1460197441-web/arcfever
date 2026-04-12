const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '评价列表加载失败',
    icon: 'none'
  });
}

Page({
  data: { list: [] },
  onLoad() {
    callService('getRatingList')
      .then((res) => this.setData({ list: res.list }))
      .catch(showError);
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  goPublish() {
    wx.navigateTo({ url: '/pages/rating-publish/index' });
  }
});
