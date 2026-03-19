const { callService } = require('../../utils/api');

Page({
  data: {
    loading: true,
    categories: [],
    schools: []
  },
  onLoad() {
    callService('getCategories').then((res) => {
      this.setData({
        loading: false,
        categories: res.categories.filter((item) => item !== '全部'),
        schools: res.schools
      });
    });
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
