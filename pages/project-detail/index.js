const { callService } = require('../../utils/api');

Page({
  data: {
    loading: true,
    project: null,
    flow: [],
    matrix: [],
    keywordsText: ''
  },
  onLoad(options) {
    this.loadData(options.id);
  },
  loadData(id) {
    callService('getProjectDetail', { id })
      .then((res) => {
        this.setData({
          loading: false,
          project: res.project,
          flow: res.flow,
          matrix: res.matrix,
          keywordsText: res.project.keywords.join(' / ')
        });
      })
      .catch(() => {
        wx.showToast({ title: '项目详情加载失败', icon: 'none' });
        this.setData({ loading: false });
      });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  contactPlatform() {
    wx.showModal({
      title: '联系平台',
      content: '当前版本已完成业务闭环演示，你可以继续接入微信客服、企业微信或表单系统。',
      showCancel: false
    });
  }
});
