const { callService } = require('../../utils/api');

Page({
  data: { list: [] },
  onLoad() {
    callService('getChatList').then((res) => this.setData({ list: res.list }));
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  openChat(event) {
    wx.navigateTo({ url: `/pages/chat-detail/index?id=${event.currentTarget.dataset.id}` });
  }
});
