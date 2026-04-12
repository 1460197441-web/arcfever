const { callService } = require('../../utils/api');

const DISPUTE_REASONS = [
  '设备参数与描述不一致',
  '交付时存在损坏或旧痕争议',
  '排期 / 发货进度异常，申请平台介入'
];

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '操作失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    order: null,
    instrument: null,
    agreement: null,
    chatId: ''
  },
  onLoad(options) {
    this.orderId = options.id;
    this.loadData();
  },
  loadData() {
    callService('getOrderDetail', { id: this.orderId })
      .then((res) => {
        this.setData({
          order: res.order,
          instrument: res.instrument,
          agreement: res.agreement,
          chatId: res.chatId || ''
        });
      })
      .catch(showError);
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  goAgreement() {
    const instrumentId = this.data.instrument && this.data.instrument.id;
    wx.navigateTo({
      url: instrumentId ? `/pages/agreement/index?instrumentId=${instrumentId}` : '/pages/agreement/index'
    });
  },
  goChat() {
    if (this.data.chatId) {
      wx.navigateTo({ url: `/pages/chat-detail/index?id=${this.data.chatId}` });
      return;
    }
    if (!this.data.instrument) {
      wx.showToast({ title: '当前订单还没有可用会话', icon: 'none' });
      return;
    }
    callService('ensureInstrumentChat', {
      instrumentId: this.data.instrument.id
    })
      .then((res) => {
        this.setData({ chatId: res.chatId });
        wx.navigateTo({ url: `/pages/chat-detail/index?id=${res.chatId}` });
      })
      .catch(showError);
  },
  goRating() {
    if (!this.data.instrument) {
      wx.showToast({ title: '当前订单暂不支持评价', icon: 'none' });
      return;
    }
    wx.navigateTo({
      url: `/pages/rating-publish/index?orderId=${this.data.order.id}&target=${encodeURIComponent(this.data.instrument.name)}`
    });
  },
  raiseDispute() {
    if (!this.data.order || !this.data.order.disputeEligible) {
      wx.showToast({ title: '当前订单暂不支持发起纠纷', icon: 'none' });
      return;
    }
    wx.showActionSheet({
      itemList: DISPUTE_REASONS,
      success: ({ tapIndex }) => {
        callService('createDispute', {
          orderId: this.data.order.id,
          summary: DISPUTE_REASONS[tapIndex]
        })
          .then((res) => {
            wx.showToast({ title: res.message, icon: 'none' });
            this.loadData();
          })
          .catch(showError);
      }
    });
  }
});
