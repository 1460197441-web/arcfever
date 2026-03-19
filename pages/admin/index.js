const { callService } = require('../../utils/api');

Page({
  data: { stats: null },
  onLoad() {
    callService('getAdminDashboard').then((stats) => this.setData({ stats }));
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  goSchoolManage() {
    wx.navigateTo({ url: '/pages/admin-schools/index' });
  }
});
