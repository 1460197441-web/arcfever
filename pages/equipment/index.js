const { callService } = require('../../utils/api');

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
      activeCategory: options.category || '全部'
    });
    this.loadData();
  },
  loadData() {
    const { activeCategory, keyword } = this.data;
    callService('getInstruments', {
      category: activeCategory,
      keyword
    }).then((res) => {
      this.setData({
        loading: false,
        categories: res.categories,
        list: res.list
      });
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
