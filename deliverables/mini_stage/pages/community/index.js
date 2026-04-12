const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '社区加载失败',
    icon: 'none'
  });
}

Page({
  data: {
    loading: true,
    tags: [],
    activeTag: '全部',
    list: [],
    filteredList: []
  },
  onLoad() {
    this.loadData();
  },
  loadData() {
    callService('getCommunity')
      .then((res) => {
        this.setData({
          loading: false,
          tags: res.tags,
          activeTag: res.tags[0] || '全部',
          list: res.list,
          filteredList: res.list
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
  chooseTag(event) {
    const activeTag = event.currentTarget.dataset.tag;
    const filteredList =
      activeTag === '全部' ? this.data.list : this.data.list.filter((item) => item.tag === activeTag);
    this.setData({ activeTag, filteredList });
  },
  openPost(event) {
    wx.navigateTo({
      url: `/pages/post-detail/index?id=${event.currentTarget.dataset.id}`
    });
  }
});
