const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '操作失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    chat: null,
    messages: [],
    inputText: ''
  },
  onLoad(options) {
    this.chatId = options.id || '';
    if (!this.chatId) {
      wx.showToast({ title: '缺少会话信息', icon: 'none' });
      return;
    }
    this.loadData();
  },
  loadData() {
    callService('getChatDetail', { id: this.chatId })
      .then((res) => {
        this.setData({
          chat: res.chat,
          messages: res.messages
        });
      })
      .catch(showError);
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    this.setData({ inputText: event.detail.value });
  },
  sendMessage() {
    if (!this.data.inputText.trim()) {
      wx.showToast({ title: '请输入消息内容', icon: 'none' });
      return;
    }
    callService('sendChatMessage', {
      chatId: this.chatId,
      text: this.data.inputText
    })
      .then((res) => {
        this.setData({
          messages: res.messages,
          inputText: ''
        });
      })
      .catch(showError);
  },
  requestSupport() {
    callService('requestSupportIntervention', {
      chatId: this.chatId
    })
      .then(() => {
        wx.showToast({ title: '平台客服已介入', icon: 'none' });
        this.loadData();
      })
      .catch(showError);
  },
  openInstrument() {
    const instrumentId = this.data.chat && this.data.chat.instrumentId;
    if (!instrumentId) return;
    wx.navigateTo({
      url: `/pages/equipment-detail/index?id=${instrumentId}`
    });
  },
  openOrder() {
    const orderId = this.data.chat && this.data.chat.orderId;
    if (!orderId) return;
    wx.navigateTo({
      url: `/pages/order-detail/index?id=${orderId}`
    });
  }
});
