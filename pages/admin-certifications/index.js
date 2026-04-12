const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '操作失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    list: []
  },
  onShow() {
    this.loadData();
  },
  loadData() {
    callService('getCertificationList')
      .then((res) => this.setData({ list: res.list }))
      .catch(showError);
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  review(event) {
    const { id, status } = event.currentTarget.dataset;
    callService('reviewCertification', { id, status })
      .then((res) => {
        wx.showToast({ title: res.message, icon: 'none' });
        this.loadData();
      })
      .catch(showError);
  }
});
