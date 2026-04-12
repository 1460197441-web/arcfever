const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '首页加载失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    loading: true,
    homeData: null,
    categories: ['全部', '海洋观测', '地质灾害', '生物材料', '化学分析', '高精仪器']
  },
  onLoad() {
    this.loadData();
  },
  onShow() {
    this.syncTabBar();
  },
  loadData() {
    callService('getHomeData')
      .then((homeData) => {
        this.setData({ homeData, loading: false });
      })
      .catch((error) => {
        this.setData({ loading: false });
        showError(error);
      });
  },
  syncTabBar() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().syncSelected();
    }
  },
  goPage(event) {
    wx.navigateTo({ url: event.currentTarget.dataset.page });
  },
  openInstrument(event) {
    wx.navigateTo({
      url: `/pages/equipment-detail/index?id=${event.currentTarget.dataset.id}`
    });
  },
  openCategory(event) {
    wx.navigateTo({
      url: `/pages/equipment/index?category=${event.currentTarget.dataset.category}`
    });
  }
});
