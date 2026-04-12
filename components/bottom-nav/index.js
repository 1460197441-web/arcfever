Component({
  properties: {
    active: {
      type: String,
      value: 'home'
    }
  },
  methods: {
    go(event) {
      const key = event.currentTarget.dataset.key;
      const page = event.currentTarget.dataset.page;
      if (key === this.data.active) return;
      wx.reLaunch({ url: page });
    }
  }
});
