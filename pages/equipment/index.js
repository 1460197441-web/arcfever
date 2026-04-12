const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '仪器列表加载失败',
    icon: 'none'
  });
}

Page({
  data: {
    loading: true,
    keyword: '',
    categories: [],
    activeCategory: '全部',
    list: []
  },
  onLoad(options) {
    this.setData({
      activeCategory: options.category ? decodeURIComponent(options.category) : '全部',
      keyword: options.keyword ? decodeURIComponent(options.keyword) : ''
    });
    this.loadData();
  },
  loadData() {
    const { activeCategory, keyword } = this.data;
    callService('getInstruments', {
      category: activeCategory,
      keyword
    })
      .then((res) => {
        this.setData({
          loading: false,
          categories: res.categories,
          list: res.list
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
  onKeywordInput(event) {
    this.setData({ keyword: event.detail.value });
    this.loadData();
  },
  chooseCategory(event) {
    this.setData({ activeCategory: event.currentTarget.dataset.category });
    this.loadData();
  },
  openInstrument(event) {
    wx.navigateTo({
      url: `/pages/equipment-detail/index?id=${event.currentTarget.dataset.id}`
    });
  },
  goCart() {
    wx.navigateTo({ url: '/pages/cart/index' });
  }
});
