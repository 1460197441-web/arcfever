const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '帖子加载失败',
    icon: 'none'
  });
}

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
      .catch((error) => {
        this.setData({ loading: false });
        showError(error);
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
