const { callService } = require('../../utils/api');

Page({
  data: { order: null, instrument: null },
  onLoad(options) {
    callService('getOrderDetail', { id: options.id }).then((res) => {
      this.setData({ order: res.order, instrument: res.instrument });
    });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  }
});
