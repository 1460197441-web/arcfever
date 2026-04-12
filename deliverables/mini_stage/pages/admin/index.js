const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '后台数据加载失败',
    icon: 'none'
  });
}

Page({
  data: { stats: null },
  onShow() {
    callService('getAdminDashboard')
      .then((stats) => this.setData({ stats }))
      .catch(showError);
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  goSchoolManage() {
    wx.navigateTo({ url: '/pages/admin-schools/index' });
  },
  goPage(event) {
    wx.navigateTo({ url: event.currentTarget.dataset.page });
  }
});
