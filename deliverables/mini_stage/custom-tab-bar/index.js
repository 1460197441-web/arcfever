Component({
  data: {
    selected: 0,
    list: [
      { pagePath: 'pages/home/index', text: '首页', key: 'home' },
      { pagePath: 'pages/category/index', text: '分类', key: 'category' },
      { pagePath: 'pages/instrument-publish/index', text: '发布', key: 'publish' },
      { pagePath: 'pages/chat-list/index', text: '消息', key: 'chat' },
      { pagePath: 'pages/profile/index', text: '我的', key: 'profile' }
    ]
  },
  lifetimes: {
    attached() {
      this.syncSelected();
    }
  },
  pageLifetimes: {
    show() {
      this.syncSelected();
    }
  },
  methods: {
    syncSelected() {
      const pages = getCurrentPages();
      const current = pages[pages.length - 1];
      const route = current && current.route;
      const selected = this.data.list.findIndex((item) => item.pagePath === route);
      if (selected >= 0 && selected !== this.data.selected) {
        this.setData({ selected });
      }
    },
    switchTab(event) {
      const index = Number(event.currentTarget.dataset.index);
      const item = this.data.list[index];
      if (!item || index === this.data.selected) return;
      wx.switchTab({
        url: `/${item.pagePath}`
      });
    }
  }
});
