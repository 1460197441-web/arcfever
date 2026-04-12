const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '项目加载失败',
    icon: 'none'
  });
}

Page({
  data: {
    loading: true,
    filters: [],
    activeFilter: '全部',
    list: [],
    filteredList: []
  },
  onLoad() {
    this.loadData();
  },
  loadData() {
    callService('getProjects')
      .then((res) => {
        this.setData({
          loading: false,
          filters: res.filters,
          activeFilter: res.filters[0] || '全部',
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
  chooseFilter(event) {
    const activeFilter = event.currentTarget.dataset.filter;
    const filteredList =
      activeFilter === '全部'
        ? this.data.list
        : this.data.list.filter((item) => item.status === activeFilter);
    this.setData({ activeFilter, filteredList });
  },
  openProject(event) {
    wx.navigateTo({
      url: `/pages/project-detail/index?id=${event.currentTarget.dataset.id}`
    });
  },
  goPublish() {
    wx.navigateTo({ url: '/pages/publish-project/index' });
  }
});
