const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '项目详情加载失败',
    icon: 'none'
  });
}

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
          keywordsText: (res.project.keywords || []).join(' / ')
        });
      })
      .catch((error) => {
        this.setData({ loading: false });
        showError(error);
      });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  contactPlatform() {
    wx.showModal({
      title: '联系平台',
      content: '当前版本已打通项目协作展示流程，后续可以继续接入客服、企业微信或线索表单。',
      showCancel: false
    });
  }
});
