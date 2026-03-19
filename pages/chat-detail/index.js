const { callService } = require('../../utils/api');

Page({
  data: { chat: null, messages: [] },
  onLoad(options) {
    callService('getChatDetail', { id: options.id }).then((res) => {
      this.setData({ chat: res.chat, messages: res.messages });
    });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  }
});
