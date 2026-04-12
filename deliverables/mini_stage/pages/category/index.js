const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '分类加载失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    loading: true,
    categories: [],
    schools: []
  },
  onLoad() {
    callService('getCategories')
      .then((res) => {
        this.setData({
          loading: false,
          categories: res.categories.filter((item) => item !== '全部'),
          schools: res.schools.map((item) => ({
            ...item,
            collegesText: item.colleges.join(' / ')
          }))
        });
      })
      .catch((error) => {
        this.setData({ loading: false });
        showError(error);
      });
  },
  onShow() {
    this.syncTabBar();
  },
  syncTabBar() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().syncSelected();
    }
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  openCategory(event) {
    wx.navigateTo({
      url: `/pages/equipment/index?category=${event.currentTarget.dataset.category}`
    });
  }
});
