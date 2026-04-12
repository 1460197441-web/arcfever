const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '首页加载失败，请稍后重试',
    icon: 'none'
  });
}

function normalizeInstrumentMedia(item = {}) {
  const images = Array.isArray(item.images) ? item.images.filter(Boolean) : [];
  return {
    ...item,
    coverImage: item.coverImage || images[0] || ''
  };
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
        this.setData({
          homeData: {
            ...homeData,
            featuredInstruments: (homeData.featuredInstruments || []).map(normalizeInstrumentMedia)
          },
          loading: false
        });
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
  openInstrument(event) {
    wx.navigateTo({
      url: `/pages/equipment-detail/index?id=${event.currentTarget.dataset.id}`
    });
  },
  openCategory(event) {
    const app = getApp();
    app.globalData.prefillCategory = event.currentTarget.dataset.category || '';
    wx.switchTab({
      url: '/pages/category/index'
    });
  }
});
