const { callService } = require('../../utils/api');

Page({
  data: {
    loading: true,
    post: null,
    related: []
  },
  onLoad(options) {
    this.loadData(options.id);
  },
  loadData(id) {
    callService('getPostDetail', { id })
      .then((res) => {
        this.setData({
          loading: false,
          post: res.post,
          related: res.related
        });
      })
      .catch(() => {
        wx.showToast({ title: '帖子加载失败', icon: 'none' });
        this.setData({ loading: false });
      });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  openPost(event) {
    wx.redirectTo({
      url: `/pages/post-detail/index?id=${event.currentTarget.dataset.id}`
    });
  }
});
